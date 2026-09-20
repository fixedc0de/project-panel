const express = require('express');
const pidusage = require('pidusage');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();

// Helper: Get stats untuk satu bot
async function getBotStats(botId, runningBots) {
    const bot = runningBots.get(botId);
    if (!bot || !bot.process || !bot.process.pid) {
        return {
            botId,
            running: false,
            cpu: 0,
            memory: 0,
            memoryMB: 0,
            pid: null,
            uptime: 0
        };
    }

    try {
        const stats = await pidusage(bot.process.pid);
        const uptime = Math.floor((Date.now() - bot.startedAt.getTime()) / 1000);
        
        return {
            botId,
            running: true,
            cpu: stats.cpu.toFixed(2),
            memory: stats.memory,
            memoryMB: (stats.memory / 1024 / 1024).toFixed(2),
            pid: stats.pid,
            uptime: uptime,
            uptimeFormatted: formatUptime(uptime)
        };
    } catch (err) {
        console.error(`Error getting stats for ${botId}:`, err.message);
        return {
            botId,
            running: false,
            cpu: 0,
            memory: 0,
            memoryMB: 0,
            pid: null,
            uptime: 0,
            error: err.message
        };
    }
}

function formatUptime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h}h ${m}m ${s}s`;
}

// ===================== GET: Stats untuk semua bot user =====================
router.get('/my-bots', authenticateToken, async (req, res) => {
    try {
        const db = require('../config/database');
        const result = await db.query(
            'SELECT bot_name FROM bots WHERE user_id = $1',
            [req.user.id]
        );

        // Import runningBots dari server.js via global
        const runningBots = global.runningBots;
        if (!runningBots) {
            return res.status(500).json({ error: 'Server not ready' });
        }

        const stats = await Promise.all(
            result.rows.map(row => getBotStats(row.bot_name, runningBots))
        );

        res.json(stats);
    } catch (err) {
        console.error('Monitoring error:', err);
        res.status(500).json({ error: 'Gagal mengambil monitoring data' });
    }
});

// ===================== GET: Stats untuk semua bot (Admin) =====================
router.get('/all-bots', authenticateToken, async (req, res) => {
    try {
        if (req.user.role !== 'admin') {
            return res.status(403).json({ error: 'Admin only' });
        }

        const db = require('../config/database');
        const result = await db.query(`
            SELECT b.bot_name, u.username, u.telegram_id 
            FROM bots b 
            JOIN users u ON b.user_id = u.id
        `);

        const runningBots = global.runningBots;
        if (!runningBots) {
            return res.status(500).json({ error: 'Server not ready' });
        }

        const stats = await Promise.all(
            result.rows.map(row => getBotStats(row.bot_name, runningBots).then(s => ({
                ...s,
                owner: row.username || row.telegram_id
            })))
        );

        res.json(stats);
    } catch (err) {
        console.error('Admin monitoring error:', err);
        res.status(500).json({ error: 'Gagal mengambil monitoring data' });
    }
});

// ===================== GET: System-wide stats =====================
router.get('/system', authenticateToken, async (req, res) => {
    try {
        if (req.user.role !== 'admin') {
            return res.status(403).json({ error: 'Admin only' });
        }

        const os = require('os');
        const runningBots = global.runningBots || new Map();

        // Hitung total resource yang dipakai semua bot
        let totalCpu = 0;
        let totalMemory = 0;
        let runningCount = 0;

        for (const [botId, bot] of runningBots.entries()) {
            if (bot.process && bot.process.pid) {
                try {
                    const stats = await pidusage(bot.process.pid);
                    totalCpu += stats.cpu;
                    totalMemory += stats.memory;
                    runningCount++;
                } catch (err) {
                    // Skip bot yang error
                }
            }
        }

        res.json({
            system: {
                totalMemory: os.totalmem(),
                freeMemory: os.freemem(),
                usedMemory: os.totalmem() - os.freemem(),
                cpuCount: os.cpus().length,
                platform: os.platform(),
                uptime: os.uptime()
            },
            bots: {
                totalRunning: runningCount,
                totalCpu: totalCpu.toFixed(2),
                totalMemoryMB: (totalMemory / 1024 / 1024).toFixed(2)
            }
        });
    } catch (err) {
        console.error('System stats error:', err);
        res.status(500).json({ error: 'Gagal mengambil system stats' });
    }
});

module.exports = router;