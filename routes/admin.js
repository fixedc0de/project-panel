const express = require('express');
const db = require('../config/database');
const { authenticateToken, requireAdmin } = require('../middleware/auth');
const { spawn } = require('child_process'); // Untuk force stop bot

const router = express.Router();

// Middleware: Hanya admin yang bisa akses route di file ini
router.use(authenticateToken, requireAdmin);

// 1. GET: System Statistics
router.get('/stats', async (req, res) => {
    try {
        const totalUsers = await db.query('SELECT COUNT(*) FROM users');
        const activeUsers = await db.query("SELECT COUNT(*) FROM users WHERE status = 'active'");
        const totalBots = await db.query('SELECT COUNT(*) FROM bots');
        const runningBots = await db.query("SELECT COUNT(*) FROM bots WHERE status = 'running'");

        res.json({
            totalUsers: parseInt(totalUsers.rows[0].count),
            activeUsers: parseInt(activeUsers.rows[0].count),
            totalBots: parseInt(totalBots.rows[0].count),
            runningBots: parseInt(runningBots.rows[0].count)
        });
    } catch (err) {
        console.error('Stats error:', err);
        res.status(500).json({ error: 'Gagal mengambil statistik' });
    }
});

// 2. GET: Daftar Semua User
router.get('/users', async (req, res) => {
    try {
        const result = await db.query(
            'SELECT id, telegram_id, username, role, status, created_at, last_login FROM users ORDER BY created_at DESC'
        );
        res.json(result.rows);
    } catch (err) {
        res.status(500).json({ error: 'Gagal mengambil data user' });
    }
});

// 3. POST: Ban / Unban User
router.post('/users/:id/toggle-ban', async (req, res) => {
    try {
        const { id } = req.params;
        // Cek status saat ini
        const currentUser = await db.query('SELECT status FROM users WHERE id = $1', [id]);
        if (currentUser.rows.length === 0) return res.status(404).json({ error: 'User tidak ditemukan' });

        const newStatus = currentUser.rows[0].status === 'banned' ? 'active' : 'banned';
        
        await db.query('UPDATE users SET status = $1 WHERE id = $2', [newStatus, id]);
        
        // Jika dibanned, stop semua bot milik user ini
        if (newStatus === 'banned') {
            const userBots = await db.query('SELECT bot_name FROM bots WHERE user_id = $1', [id]);
            // Logic stop bot akan ditangani di sini atau via server.js global map
        }

        res.json({ success: true, message: `User berhasil di-${newStatus === 'banned' ? 'ban' : 'unban'}` });
    } catch (err) {
        res.status(500).json({ error: 'Gagal mengubah status user' });
    }
});

// 4. GET: Daftar Semua Bot (Global)
router.get('/bots', async (req, res) => {
    try {
        const result = await db.query(`
            SELECT b.id, b.bot_name, b.template_id, b.status, b.created_at, u.telegram_id, u.username 
            FROM bots b 
            JOIN users u ON b.user_id = u.id 
            ORDER BY b.created_at DESC
        `);
        res.json(result.rows);
    } catch (err) {
        res.status(500).json({ error: 'Gagal mengambil data bot global' });
    }
});

// 5. POST: Force Stop Bot (Admin)
router.post('/bots/:name/force-stop', async (req, res) => {
    try {
        const { name } = req.params;
        
        // Update status di database
        await db.query("UPDATE bots SET status = 'stopped' WHERE bot_name = $1", [name]);
        
        // Emit event ke socket (opsional, untuk update real-time di dashboard user)
        // io.emit('bot-stopped', { botId: name, code: 999, adminAction: true });

        res.json({ success: true, message: `Bot ${name} berhasil dihentikan paksa` });
    } catch (err) {
        res.status(500).json({ error: 'Gagal menghentikan bot' });
    }
});

module.exports = router;