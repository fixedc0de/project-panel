const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');
const db = require('../config/database');
const officialBot = require('../services/telegramBot');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();

// Rate limiter: max 5 request per 15 menit per IP
const registerLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 5,
    message: { error: 'Terlalu banyak percobaan. Coba lagi 15 menit lagi.' }
});

const verifyLimiter = rateLimit({
    windowMs: 10 * 60 * 1000,
    max: 10,
    message: { error: 'Terlalu banyak percobaan verifikasi. Coba lagi nanti.' }
});

// Helper: Generate 6-digit code
function generateCode() {
    return Math.floor(100000 + Math.random() * 900000).toString();
}

// ===================== REGISTER =====================
router.post('/register', registerLimiter, async (req, res) => {
    try {
        const { telegram_id, username, password } = req.body;

        // Validasi input
        if (!telegram_id || !password) {
            return res.status(400).json({ error: 'Telegram ID dan password wajib diisi' });
        }
        if (!/^\d{6,15}$/.test(telegram_id)) {
            return res.status(400).json({ error: 'Telegram ID tidak valid (harus angka 6-15 digit)' });
        }
        if (password.length < 6) {
            return res.status(400).json({ error: 'Password minimal 6 karakter' });
        }

        // Cek apakah telegram_id sudah terdaftar
        const existing = await db.query(
            'SELECT id, status FROM users WHERE telegram_id = $1',
            [telegram_id]
        );

        if (existing.rows.length > 0) {
            const user = existing.rows[0];
            if (user.status === 'active') {
                return res.status(400).json({ error: 'Telegram ID sudah terdaftar. Silakan login.' });
            }
            if (user.status === 'pending') {
                return res.status(400).json({ 
                    error: 'Akun sedang menunggu verifikasi. Cek Telegram Anda untuk kode.',
                    needVerification: true 
                });
            }
        }

        // Hash password
        const passwordHash = await bcrypt.hash(password, 10);

        // Simpan user (status pending)
        await db.query(
            `INSERT INTO users (telegram_id, username, password_hash, status) 
             VALUES ($1, $2, $3, 'pending')
             ON CONFLICT (telegram_id) DO UPDATE 
             SET password_hash = $3, status = 'pending', username = $2`,
            [telegram_id, username || null, passwordHash]
        );

        // Generate kode verifikasi
        const code = generateCode();
        const expiresAt = new Date(Date.now() + 10 * 60 * 1000); // 10 menit

        // Hapus kode lama (jika ada)
        await db.query(
            'UPDATE verification_codes SET used = TRUE WHERE telegram_id = $1 AND used = FALSE',
            [telegram_id]
        );

        // Simpan kode baru
        await db.query(
            `INSERT INTO verification_codes (telegram_id, code, expires_at) 
             VALUES ($1, $2, $3)`,
            [telegram_id, code, expiresAt]
        );

        // Kirim kode via bot
        try {
            await officialBot.sendVerificationCode(telegram_id, code);
        } catch (err) {
            // Rollback jika gagal kirim
            await db.query('DELETE FROM users WHERE telegram_id = $1 AND status = \'pending\'', [telegram_id]);
            return res.status(400).json({ error: err.message });
        }

        res.json({ 
            success: true, 
            message: 'Kode verifikasi telah dikirim ke Telegram Anda. Silakan cek pesan.',
            telegram_id 
        });

    } catch (err) {
        console.error('Register error:', err);
        res.status(500).json({ error: 'Terjadi kesalahan server' });
    }
});

// ===================== VERIFY CODE =====================
router.post('/verify', verifyLimiter, async (req, res) => {
    try {
        const { telegram_id, code } = req.body;

        if (!telegram_id || !code) {
            return res.status(400).json({ error: 'Telegram ID dan kode wajib diisi' });
        }

        // Cari kode verifikasi yang valid
        const result = await db.query(
            `SELECT * FROM verification_codes 
             WHERE telegram_id = $1 
               AND code = $2 
               AND used = FALSE 
               AND expires_at > NOW()
             ORDER BY created_at DESC 
             LIMIT 1`,
            [telegram_id, code]
        );

        if (result.rows.length === 0) {
            // Cek apakah kode expired
            const expired = await db.query(
                `SELECT * FROM verification_codes 
                 WHERE telegram_id = $1 AND code = $2 AND used = FALSE
                 ORDER BY created_at DESC LIMIT 1`,
                [telegram_id, code]
            );

            if (expired.rows.length > 0) {
                return res.status(400).json({ error: 'Kode sudah expired. Silakan daftar ulang.' });
            }

            return res.status(400).json({ error: 'Kode verifikasi tidak valid' });
        }

        const verification = result.rows[0];

        // Cek jumlah percobaan
        if (verification.attempts >= 5) {
            return res.status(400).json({ error: 'Terlalu banyak percobaan. Silakan daftar ulang.' });
        }

        // Update status user menjadi active
        await db.query(
            `UPDATE users SET status = 'active' WHERE telegram_id = $1`,
            [telegram_id]
        );

        // Tandai kode sebagai used
        await db.query(
            `UPDATE verification_codes SET used = TRUE WHERE id = $1`,
            [verification.id]
        );

        // Ambil data user untuk kirim welcome
        const user = await db.query(
            'SELECT username FROM users WHERE telegram_id = $1',
            [telegram_id]
        );

        // Kirim pesan selamat datang
        try {
            await officialBot.sendWelcomeMessage(telegram_id, user.rows[0].username);
        } catch (err) {
            console.error('Gagal kirim welcome:', err.message);
        }

        res.json({ 
            success: true, 
            message: 'Verifikasi berhasil! Akun Anda sudah aktif. Silakan login.' 
        });

    } catch (err) {
        console.error('Verify error:', err);
        res.status(500).json({ error: 'Terjadi kesalahan server' });
    }
});

// ===================== RESEND CODE =====================
router.post('/resend-code', registerLimiter, async (req, res) => {
    try {
        const { telegram_id } = req.body;

        const user = await db.query(
            'SELECT id FROM users WHERE telegram_id = $1 AND status = \'pending\'',
            [telegram_id]
        );

        if (user.rows.length === 0) {
            return res.status(404).json({ error: 'User tidak ditemukan atau sudah aktif' });
        }

        // Generate kode baru
        const code = generateCode();
        const expiresAt = new Date(Date.now() + 10 * 60 * 1000);

        await db.query(
            'UPDATE verification_codes SET used = TRUE WHERE telegram_id = $1 AND used = FALSE',
            [telegram_id]
        );

        await db.query(
            `INSERT INTO verification_codes (telegram_id, code, expires_at) 
             VALUES ($1, $2, $3)`,
            [telegram_id, code, expiresAt]
        );

        await officialBot.sendVerificationCode(telegram_id, code);

        res.json({ success: true, message: 'Kode baru telah dikirim ke Telegram Anda' });

    } catch (err) {
        console.error('Resend error:', err);
        res.status(500).json({ error: err.message || 'Gagal mengirim ulang kode' });
    }
});

// ===================== LOGIN =====================
router.post('/login', async (req, res) => {
    try {
        const { telegram_id, password } = req.body;

        if (!telegram_id || !password) {
            return res.status(400).json({ error: 'Telegram ID dan password wajib diisi' });
        }

        const result = await db.query(
            'SELECT * FROM users WHERE telegram_id = $1',
            [telegram_id]
        );

        if (result.rows.length === 0) {
            return res.status(401).json({ error: 'Telegram ID atau password salah' });
        }

        const user = result.rows[0];

        // Cek status akun
        if (user.status === 'pending') {
            return res.status(403).json({ 
                error: 'Akun belum diverifikasi. Silakan cek Telegram Anda.',
                needVerification: true 
            });
        }
        if (user.status === 'banned') {
            return res.status(403).json({ error: 'Akun Anda telah dibanned. Hubungi admin.' });
        }

        // Verifikasi password
        const validPassword = await bcrypt.compare(password, user.password_hash);
        if (!validPassword) {
            return res.status(401).json({ error: 'Telegram ID atau password salah' });
        }

        // Update last login
        await db.query(
            'UPDATE users SET last_login = NOW() WHERE id = $1',
            [user.id]
        );

        // Generate JWT token (valid 7 hari)
        const token = jwt.sign(
            { 
                id: user.id, 
                telegram_id: user.telegram_id, 
                username: user.username,
                role: user.role 
            },
            process.env.JWT_SECRET,
            { expiresIn: '7d' }
        );

        res.json({
            success: true,
            token,
            user: {
                id: user.id,
                telegram_id: user.telegram_id,
                username: user.username,
                role: user.role
            }
        });

    } catch (err) {
        console.error('Login error:', err);
        res.status(500).json({ error: 'Terjadi kesalahan server' });
    }
});

// ===================== GET CURRENT USER =====================
router.get('/me', authenticateToken, async (req, res) => {
    try {
        const result = await db.query(
            'SELECT id, telegram_id, username, role, status, created_at, last_login FROM users WHERE id = $1',
            [req.user.id]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'User tidak ditemukan' });
        }

        res.json(result.rows[0]);
    } catch (err) {
        console.error('Get me error:', err);
        res.status(500).json({ error: 'Terjadi kesalahan server' });
    }
});

// ===================== LOGOUT (Client-side only, tapi endpoint ini untuk info) =====================
router.post('/logout', authenticateToken, (req, res) => {
    res.json({ success: true, message: 'Logout berhasil. Token dihapus di client.' });
});

// ===================== GET PROFILE =====================
router.get('/profile', authenticateToken, async (req, res) => {
    try {
        const result = await db.query(
            `SELECT id, telegram_id, username, role, status, created_at, last_login 
             FROM users WHERE id = $1`,
            [req.user.id]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'User tidak ditemukan' });
        }

        // Hitung jumlah bot milik user
        const botCount = await db.query(
            'SELECT COUNT(*) FROM bots WHERE user_id = $1',
            [req.user.id]
        );

        res.json({
            ...result.rows[0],
            bot_count: parseInt(botCount.rows[0].count)
        });
    } catch (err) {
        console.error('Get profile error:', err);
        res.status(500).json({ error: 'Gagal memuat profil' });
    }
});

// ===================== CHANGE PASSWORD =====================
router.post('/change-password', authenticateToken, async (req, res) => {
    try {
        const { current_password, new_password, confirm_password } = req.body;

        // Validasi input
        if (!current_password || !new_password || !confirm_password) {
            return res.status(400).json({ error: 'Semua field wajib diisi' });
        }

        if (new_password.length < 6) {
            return res.status(400).json({ error: 'Password baru minimal 6 karakter' });
        }

        if (new_password !== confirm_password) {
            return res.status(400).json({ error: 'Konfirmasi password tidak cocok' });
        }

        if (current_password === new_password) {
            return res.status(400).json({ error: 'Password baru tidak boleh sama dengan password lama' });
        }

        // Ambil user dari database
        const result = await db.query(
            'SELECT password_hash FROM users WHERE id = $1',
            [req.user.id]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'User tidak ditemukan' });
        }

        // Verifikasi password lama
        const validPassword = await bcrypt.compare(current_password, result.rows[0].password_hash);
        if (!validPassword) {
            return res.status(401).json({ error: 'Password lama salah' });
        }

        // Hash password baru
        const newPasswordHash = await bcrypt.hash(new_password, 10);

        // Update password
        await db.query(
            'UPDATE users SET password_hash = $1 WHERE id = $2',
            [newPasswordHash, req.user.id]
        );

        res.json({ 
            success: true, 
            message: 'Password berhasil diubah! Silakan login ulang.' 
        });

    } catch (err) {
        console.error('Change password error:', err);
        res.status(500).json({ error: 'Gagal mengubah password' });
    }
});

// ===================== UPDATE USERNAME =====================
router.post('/update-username', authenticateToken, async (req, res) => {
    try {
        const { username } = req.body;

        if (!username || username.trim().length < 3) {
            return res.status(400).json({ error: 'Username minimal 3 karakter' });
        }

        if (username.length > 50) {
            return res.status(400).json({ error: 'Username maksimal 50 karakter' });
        }

        await db.query(
            'UPDATE users SET username = $1 WHERE id = $2',
            [username.trim(), req.user.id]
        );

        res.json({ success: true, message: 'Username berhasil diubah' });

    } catch (err) {
        console.error('Update username error:', err);
        res.status(500).json({ error: 'Gagal mengubah username' });
    }
});

module.exports = router;