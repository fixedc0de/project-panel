require('dotenv').config({ path: require('path').join(__dirname, '.env') });

const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const initDatabase = require('./config/init-db');
const officialBot = require('./services/telegramBot');
const { authenticateToken } = require('./middleware/auth');
const authRoutes = require('./routes/auth');
const adminRoutes = require('./routes/admin'); 
const forgotPasswordRoutes = require('./routes/forgotPassword');
const monitoringRoutes = require('./routes/monitoring');
const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const runningBots = new Map();
const BOTS_DIR = path.join(__dirname, 'bots');
const TEMPLATES_DIR = path.join(__dirname, 'templates');

if (!fs.existsSync(BOTS_DIR)) fs.mkdirSync(BOTS_DIR, { recursive: true });
if (!fs.existsSync(TEMPLATES_DIR)) fs.mkdirSync(TEMPLATES_DIR, { recursive: true });

// ===================== AUTH ROUTES (PUBLIC) =====================
app.use('/api/auth', authRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/forgot-password', forgotPasswordRoutes);
app.use('/api/monitoring', monitoringRoutes);
// ===================== PROTECTED ROUTES =====================
global.runningBots = runningBots;
// GET: Daftar templates (butuh login)
app.get('/api/templates', authenticateToken, (req, res) => {
    if (!fs.existsSync(TEMPLATES_DIR)) return res.json([]);

    const templates = fs.readdirSync(TEMPLATES_DIR)
        .filter(dir => {
            const fullPath = path.join(TEMPLATES_DIR, dir);
            return fs.statSync(fullPath).isDirectory() 
                && fs.existsSync(path.join(fullPath, 'bot.py'));
        })
        .map(dir => {
            const infoPath = path.join(TEMPLATES_DIR, dir, 'info.json');
            let info = { name: dir, description: 'Tidak ada deskripsi', icon: '🤖', commands: [] };
            if (fs.existsSync(infoPath)) {
                try {
                    info = { ...info, ...JSON.parse(fs.readFileSync(infoPath, 'utf8')) };
                } catch (e) { /* ignore */ }
            }
            return { id: dir, ...info };
        });

    res.json(templates);
});

// GET: Daftar bot milik user yang login
app.get('/api/bots', authenticateToken, async (req, res) => {
    try {
        const db = require('./config/database');
        const result = await db.query(
            'SELECT bot_name, template_id, status, created_at FROM bots WHERE user_id = $1',
            [req.user.id]
        );

        const bots = result.rows.map(row => ({
            id: row.bot_name,
            name: row.bot_name,
            template: row.template_id,
            is_active: row.status === 'running',
            description: '',
            created_at: row.created_at
        }));

        res.json(bots);
    } catch (err) {
        console.error('Get bots error:', err);
        res.status(500).json({ error: 'Gagal memuat bot' });
    }
});

// POST: Buat bot baru
app.post('/api/bots', authenticateToken, async (req, res) => {
    try {
        const { name, token, template, description } = req.body;
        const userId = req.user.id;

        if (!name || !template) {
            return res.status(400).json({ error: 'Nama bot dan template wajib dipilih' });
        }
        
        const id = name.toLowerCase().replace(/[^a-z0-9_]/g, '_');
        
        if (!/^[a-z0-9_]+$/.test(id)) {
            return res.status(400).json({ error: 'Nama hanya boleh huruf kecil, angka, dan underscore' });
        }

        const templateDir = path.join(TEMPLATES_DIR, template);
        if (!fs.existsSync(path.join(templateDir, 'bot.py'))) {
            return res.status(404).json({ error: 'Template tidak ditemukan' });
        }

        const db = require('./config/database');
        const existing = await db.query(
            'SELECT id FROM bots WHERE bot_name = $1 AND user_id = $2',
            [id, userId]
        );
        if (existing.rows.length > 0) {
            return res.status(400).json({ error: 'Nama bot sudah digunakan' });
        }

        const botDir = path.join(BOTS_DIR, id);
        if (fs.existsSync(botDir)) {
            return res.status(400).json({ error: 'Folder bot sudah ada' });
        }

        // Copy template
        fs.cpSync(templateDir, botDir, { recursive: true });
        fs.writeFileSync(
            path.join(botDir, 'config.json'),
            JSON.stringify({ token: token || '', template }, null, 2)
        );

        // Simpan ke database
        await db.query(
            `INSERT INTO bots (user_id, bot_name, template_id, token, status, description) 
             VALUES ($1, $2, $3, $4, 'stopped', $5)`,
            [userId, id, template, token || null, description || null]
        );

        res.json({ success: true, message: 'Bot berhasil dibuat!' });
    } catch (err) {
        console.error('Create bot error:', err);
        res.status(500).json({ error: 'Gagal membuat bot' });
    }
});

// POST: Toggle bot status (start/stop)
app.post('/api/bots/:id/toggle', authenticateToken, async (req, res) => {
    try {
        const { id } = req.params;
        const { is_active } = req.body;
        const userId = req.user.id;
        
        const db = require('./config/database');
        const bot = await db.query(
            'SELECT * FROM bots WHERE bot_name = $1 AND user_id = $2',
            [id, userId]
        );
        
        if (bot.rows.length === 0) {
            return res.status(403).json({ error: 'Bot tidak ditemukan atau bukan milik Anda' });
        }

        if (is_active) {
            // Start bot
            const botDir = path.join(BOTS_DIR, id);
            
            if (!fs.existsSync(path.join(botDir, 'bot.py'))) {
                return res.status(404).json({ error: 'File bot.py tidak ditemukan' });
            }
            if (runningBots.has(id)) {
                return res.status(400).json({ error: 'Bot sudah berjalan' });
            }

            let token = bot.rows[0].token || '';
            if (!token) {
                return res.status(400).json({ error: 'Token kosong' });
            }

            const pythonProcess = spawn('python', ['bot.py'], {
                cwd: botDir,
                env: {
                    ...process.env,
                    BOT_TOKEN: token,
                    BOT_ID: id,
                    PYTHONUTF8: '1',
                    PYTHONIOENCODING: 'utf-8'
                }
            });

            runningBots.set(id, { 
                process: pythonProcess, 
                token, 
                path: botDir, 
                userId,
                startedAt: new Date()
            });

            pythonProcess.stdout.on('data', (data) => {
                io.to(`user_${userId}`).emit('bot-log', { botId: id, type: 'stdout', message: data.toString() });
            });

            pythonProcess.stderr.on('data', (data) => {
                io.to(`user_${userId}`).emit('bot-log', { botId: id, type: 'stderr', message: data.toString() });
            });

            pythonProcess.on('close', async (code) => {
                io.to(`user_${userId}`).emit('bot-stopped', { botId: id, code });
                runningBots.delete(id);
                await db.query('UPDATE bots SET status = \'stopped\' WHERE bot_name = $1', [id]);
            });

            await db.query('UPDATE bots SET status = \'running\' WHERE bot_name = $1', [id]);
            res.json({ success: true, message: 'Bot dimulai' });
        } else {
            // Stop bot
            const running = runningBots.get(id);
            if (!running) {
                return res.status(400).json({ error: 'Bot tidak berjalan' });
            }

            running.process.kill('SIGTERM');
            await db.query('UPDATE bots SET status = \'stopped\' WHERE bot_name = $1', [id]);
            res.json({ success: true, message: 'Bot dihentikan' });
        }
    } catch (err) {
        console.error('Toggle bot error:', err);
        res.status(500).json({ error: 'Gagal mengubah status bot' });
    }
});

// DELETE: Hapus bot
app.delete('/api/bots/:id', authenticateToken, async (req, res) => {
    try {
        const { id } = req.params;
        const userId = req.user.id;
        
        const db = require('./config/database');
        const bot = await db.query(
            'SELECT id FROM bots WHERE bot_name = $1 AND user_id = $2',
            [id, userId]
        );
        if (bot.rows.length === 0) {
            return res.status(403).json({ error: 'Bot tidak ditemukan' });
        }

        if (runningBots.has(id)) {
            runningBots.get(id).process.kill('SIGTERM');
            runningBots.delete(id);
        }

        const botDir = path.join(BOTS_DIR, id);
        if (fs.existsSync(botDir)) {
            fs.rmSync(botDir, { recursive: true, force: true });
        }

        await db.query('DELETE FROM bots WHERE bot_name = $1', [id]);
        
        res.json({ success: true });
    } catch (err) {
        console.error('Delete bot error:', err);
        res.status(500).json({ error: 'Gagal menghapus bot' });
    }
});

// ===================== SOCKET.IO =====================
io.on('connection', (socket) => {
    console.log('Client terhubung:', socket.id);
    
    // User join room berdasarkan user_id
    socket.on('join', (userId) => {
        socket.join(`user_${userId}`);
        console.log(`User ${userId} joined room`);
    });

    socket.on('disconnect', () => console.log('Client terputus'));
});

// ===================== START SERVER =====================
const PORT = process.env.PORT || 3000;

async function startServer() {
    try {
        // Init database
        await initDatabase();
        console.log('✅ Database connected');

        // Init official bot
        await officialBot.init();

        // Start server
        server.listen(PORT, () => {
            console.log(`🚀 Panel berjalan di http://localhost:${PORT}`);
            console.log(`📂 Template: ${fs.readdirSync(TEMPLATES_DIR).length}`);
        });
    } catch (err) {
        console.error('❌ Gagal start server:', err);
        process.exit(1);
    }
}

startServer();