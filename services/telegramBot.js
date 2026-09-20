const { Telegraf } = require('telegraf');
require('dotenv').config({ path: require('path').join(__dirname, '../.env') });

class OfficialBot {
    constructor() {
        this.bot = null;
        this.botToken = process.env.OFFICIAL_BOT_TOKEN;
    }

    async init() {
        if (!this.botToken) {
            console.warn('⚠️  OFFICIAL_BOT_TOKEN tidak ditemukan di .env');
            return;
        }

        try {
            // Inisialisasi Telegraf
            this.bot = new Telegraf(this.botToken);
            
            // Test koneksi dengan mengambil info bot
            const botInfo = await this.bot.telegram.getMe();
            console.log(`✅ Official bot connected: @${botInfo.username}`);
        } catch (err) {
            console.error('❌ Official bot init error:', err.message);
        }
    }

    // Kirim kode verifikasi ke user
    async sendVerificationCode(telegramId, code) {
        if (!this.bot) {
            throw new Error('Official bot belum terinisialisasi');
        }

        const message = 
`🔐 <b>Kode Verifikasi Panel Bot</b>

Halo! Gunakan kode berikut untuk menyelesaikan pendaftaran Anda:

<code>${code}</code>

⏰ Kode berlaku selama <b>10 menit</b>.
🔒 Jangan bagikan kode ini kepada siapapun.

Jika Anda tidak merasa mendaftar, abaikan pesan ini.`;

        try {
            await this.bot.telegram.sendMessage(telegramId, message, { parse_mode: 'HTML' });
            return true;
        } catch (err) {
            console.error(`Gagal kirim kode ke ${telegramId}:`, err.message);
            
            // Handle error spesifik dari Telegraf
            if (err.description && err.description.includes('chat not found')) {
                throw new Error('Telegram ID tidak ditemukan. Pastikan Anda sudah chat @bot_official Anda minimal 1x (klik Start)!');
            }
            if (err.description && err.description.includes('bot was blocked')) {
                throw new Error('Anda telah memblokir bot. Silakan unblock terlebih dahulu.');
            }
            throw new Error('Gagal mengirim kode. Coba lagi nanti.');
        }
    }

    // Kirim notifikasi akun aktif
    async sendWelcomeMessage(telegramId, username) {
        if (!this.bot) return;

        const message = 
`✅ <b>Pendaftaran Berhasil!</b>

Halo ${username || 'User'}! Akun Anda sudah aktif.

🌐 Silakan login di panel untuk mulai membuat bot.

Terima kasih telah menggunakan layanan kami!`;

        try {
            await this.bot.telegram.sendMessage(telegramId, message, { parse_mode: 'HTML' });
        } catch (err) {
            console.error('Gagal kirim welcome message:', err.message);
        }
    }
}

module.exports = new OfficialBot();