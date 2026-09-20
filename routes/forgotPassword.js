const express = require('express');
const bcrypt = require('bcrypt');
const rateLimit = require('express-rate-limit');
const db = require('../config/database');
const officialBot = require('../services/telegramBot');

const router = express.Router();

// Rate limiter ketat untuk forgot password
const forgotLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 menit
    max: 3, // max 3 request per IP
    message: { error: 'Terlalu banyak percobaan. Coba lagi 15 menit lagi.' }
});

const resetLimiter = rateLimit({
    windowMs: 10 * 60 * 1000,
    max: 10,
    message: { error: 'Terlalu banyak percobaan reset. Coba lagi nanti.' }
});

// Helper: Generate 6-digit code
function generateCode() {
    return Math.floor(100000 + Math.random() * 900000).toString();
}

// ===================== STEP 1: REQUEST RESET CODE =====================
router.post('/request-code', forgotLimiter, async (req, res) => {
    try {
        const { telegram_id } = req.body;

        if (!telegram_id || !/^\d{6,15}$/.test(telegram_id)) {
            return res.status(400).json({ error: 'Telegram ID tidak valid' });
        }

        // Cek apakah user ada dan aktif
        const user = await db.query(
            "SELECT id, username FROM users WHERE telegram_id = $1 AND status = 'active'",
            [telegram_id]
        );

        if (user.rows.length === 0) {
            // Security: Jangan beri tahu apakah user ada atau tidak
            return res.json({ 
                success: true, 
                message: 'Jika Telegram ID terdaftar, kode reset akan dikirim ke Telegram Anda.' 
            });
        }

        // Invalidate kode lama
        await db.query(
            'UPDATE password_resets SET used = TRUE WHERE telegram_id = $1 AND used = FALSE',
            [telegram_id]
        );

        // Generate kode baru
        const code = generateCode();
        const expiresAt = new Date(Date.now() + 10 * 60 * 1000); // 10 menit

        await db.query(
            `INSERT INTO password_resets (telegram_id, code, expires_at) 
             VALUES ($1, $2, $3)`,
            [telegram_id, code, expiresAt]
        );

        // Kirim via bot
        const username = user.rows[0].username || 'User';
        const message = 
`🔑 <b>Reset Password Panel Bot</b>

Halo ${username}!

Kami menerima permintaan reset password untuk akun Anda. Gunakan kode berikut:

<code>${code}</code>

⏰ Kode berlaku selama <b>10 menit</b>.
🔒 Jangan bagikan kode ini kepada siapapun.

Jika Anda tidak merasa meminta reset password, abaikan pesan ini dan segera ganti password Anda.`;

        try {
            await officialBot.bot.telegram.sendMessage(telegram_id, message, { parse_mode: 'HTML' });
        } catch (err) {
            console.error('Gagal kirim kode reset:', err.message);
            // Rollback
            await db.query(
                'UPDATE password_resets SET used = TRUE WHERE telegram_id = $1 AND code = $2',
                [telegram_id, code]
            );
            return res.status(400).json({ error: 'Gagal mengirim kode. Pastikan Anda sudah chat bot official.' });
        }

        res.json({ 
            success: true, 
            message: 'Kode reset telah dikirim ke Telegram Anda. Cek pesan dari bot official.',
            telegram_id 
        });

    } catch (err) {
        console.error('Request code error:', err);
        res.status(500).json({ error: 'Terjadi kesalahan server' });
    }
});

// ===================== STEP 2: VERIFY CODE & RESET PASSWORD =====================
router.post('/reset-password', resetLimiter, async (req, res) => {
    try {
        const { telegram_id, code, new_password, confirm_password } = req.body;

        // Validasi input
        if (!telegram_id || !code || !new_password || !confirm_password) {
            return res.status(400).json({ error: 'Semua field wajib diisi' });
        }

        if (new_password.length < 6) {
            return res.status(400).json({ error: 'Password baru minimal 6 karakter' });
        }

        if (new_password !== confirm_password) {
            return res.status(400).json({ error: 'Konfirmasi password tidak cocok' });
        }

        // Cari kode reset yang valid
        const result = await db.query(
            `SELECT * FROM password_resets 
             WHERE telegram_id = $1 
               AND code = $2 
               AND used = FALSE 
               AND expires_at > NOW()
             ORDER BY created_at DESC 
             LIMIT 1`,
            [telegram_id, code]
        );

        if (result.rows.length === 0) {
            // Cek apakah expired
            const expired = await db.query(
                `SELECT id, attempts FROM password_resets 
                 WHERE telegram_id = $1 AND code = $2 AND used = FALSE
                 ORDER BY created_at DESC LIMIT 1`,
                [telegram_id, code]
            );

            if (expired.rows.length > 0) {
                // Update attempts
                await db.query(
                    'UPDATE password_resets SET attempts = attempts + 1 WHERE id = $1',
                    [expired.rows[0].id]
                );
                
                if (expired.rows[0].attempts >= 4) {
                    return res.status(400).json({ error: 'Kode sudah expired. Silakan minta kode baru.' });
                }
                return res.status(400).json({ error: 'Kode sudah expired. Silakan minta kode baru.' });
            }

            return res.status(400).json({ error: 'Kode verifikasi tidak valid' });
        }

        const resetRecord = result.rows[0];

        // Cek jumlah percobaan
        if (resetRecord.attempts >= 5) {
            return res.status(400).json({ error: 'Terlalu banyak percobaan. Silakan minta kode baru.' });
        }

        // Hash password baru
        const newPasswordHash = await bcrypt.hash(new_password, 10);

        // Update password user
        await db.query(
            'UPDATE users SET password_hash = $1 WHERE telegram_id = $2',
            [newPasswordHash, telegram_id]
        );

        // Tandai kode sebagai used
        await db.query(
            'UPDATE password_resets SET used = TRUE WHERE id = $1',
            [resetRecord.id]
        );

        // Kirim notifikasi sukses
        try {
            const successMsg = 
`✅ <b>Password Berhasil Direset!</b>

Password akun Anda telah berhasil diubah.

🔐 Silakan login dengan password baru Anda.

Jika Anda tidak merasa melakukan ini, segera hubungi admin.`;
            await officialBot.bot.telegram.sendMessage(telegram_id, successMsg, { parse_mode: 'HTML' });
        } catch (err) {
            console.error('Gagal kirim notifikasi:', err.message);
        }

        res.json({ 
            success: true, 
            message: 'Password berhasil direset! Silakan login dengan password baru.' 
        });

    } catch (err) {
        console.error('Reset password error:', err);
        res.status(500).json({ error: 'Terjadi kesalahan server' });
    }
});

module.exports = router;