# 🤖 Bot Panel - Platform Manajemen Bot Telegram

Platform berbasis web untuk membuat, mengelola, dan menjalankan multiple bot Telegram dengan berbagai template siap pakai. Setiap bot memiliki database SQLite terpisah untuk isolasi data.

## ✨ Fitur Utama

### 🔐 Sistem Autentikasi
- Login/Register menggunakan **Telegram ID** (bukan email)
- Verifikasi 2 langkah via bot official
- Forgot password melalui Telegram
- JWT-based authentication
- Rate limiting untuk keamanan

### 🤖 Template Bot Tersedia (7 Templates)

1. **Group Manager Bot** 🛡️
   - Welcome/Goodbye messages
   - Moderasi: warn, kick, ban, mute/unmute
   - Custom commands per grup
   - Anti-link detector
   - Stats tracking

2. **Auto Response Bot** 💬
   - Auto-response berdasarkan keyword
   - Support regex pattern matching
   - Statistik penggunaan command

3. **Utility Tools Bot** 🛠️
   - Kalkulator ilmiah
   - Quote generator & saver
   - Reminder & timer
   - Catatan pribadi
   - Unit converter
   - Random tools (coin flip, dice, decide)

4. **Echo Bot** 🔁
   - Bot sederhana yang mengulang pesan
   - Cocok untuk testing

5. **Calculator Bot** 🧮
   - Kalkulasi matematika dasar
   - Support ekspresi kompleks

6. **Info Bot** 📊
   - Informasi user dan grup
   - Statistik member

7. **Welcome Bot** 🎉
   - Pesan selamat datang custom
   - Goodbye messages

### 📊 Dashboard Web
- UI modern dengan gradient design
- Real-time bot status monitoring
- Start/Stop bot dengan satu klik
- Log output bot secara real-time (WebSocket)
- Manajemen multiple bot

### 🗄️ Database
- **PostgreSQL (Neon)** untuk panel utama
- **SQLite** untuk setiap bot (isolasi penuh)
- Schema otomatis dibuat saat startup

## 🚀 Instalasi

### Prerequisites
- Node.js >= 18.x
- Python >= 3.8
- PostgreSQL account (Neon.tech)
- Telegram Bot Token dari @BotFather

### 1. Clone & Install Dependencies

```bash
cd project-panel
npm install
pip install python-telegram-bot==21.0
```

### 2. Setup Environment (.env)

Copy file `.env.example` ke `.env`:

```bash
cp .env.example .env
```

Edit `.env` dengan konfigurasi Anda:

```env
# Database Neon PostgreSQL
DATABASE_URL=postgresql://user:password@ep-xxx-xxx.region.aws.neon.tech/bot_panel?sslmode=require

# JWT Secret (generate random)
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production

# Official Bot Token (dari @BotFather)
OFFICIAL_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Server Port
PORT=3000
NODE_ENV=development
```

### 3. Dapatkan DATABASE_URL dari Neon

1. Buka [Neon Console](https://console.neon.tech)
2. Buat project baru atau pilih yang sudah ada
3. Klik **Connection Details**
4. Copy connection string
5. Tambahkan `?sslmode=require` di akhir URL

Contoh:
```
postgresql://username:password@ep-cool-wind-123456.us-east-2.aws.neon.tech/bot_panel?sslmode=require
```

### 4. Reset Database (Opsional - Jika Ada Error)

Jalankan SQL di Neon Dashboard:

```sql
-- Buka file RESET_DATABASE.sql dan copy isinya
-- Jalankan di SQL Editor di Neon Dashboard
```

Atau gunakan psql:
```bash
psql "$DATABASE_URL" -f RESET_DATABASE.sql
```

### 5. Jalankan Server

```bash
npm start
```

Server akan berjalan di: **http://localhost:3000**

## 📱 Cara Menggunakan

### Registrasi User Baru

1. Buka http://localhost:3000/register.html
2. Masukkan **Telegram ID** Anda (bukan username!)
   - Cara cek ID: chat @userinfobot di Telegram
3. Isi username (opsional) dan password
4. Klik "Daftar & Dapatkan Kode Verifikasi"
5. Cek Telegram Anda untuk kode 6 digit dari bot official
6. Masukkan kode verifikasi
7. Akun aktif! Silakan login

### Login

1. Buka http://localhost:3000
2. Masukkan Telegram ID dan password
3. Anda akan diarahkan ke dashboard

### Membuat Bot Baru

1. Di dashboard, klik **"+ Tambah Bot"**
2. Isi form:
   - **Nama Bot**: nama unik (huruf kecil, angka, underscore)
   - **Bot Token**: dari @BotFather
   - **Template**: pilih template yang diinginkan
   - **Deskripsi**: deskripsi opsional
3. Klik **"Buat Bot"**

### Menjalankan Bot

1. Di dashboard, cari bot yang sudah dibuat
2. Klik tombol **"Start"**
3. Bot akan mulai berjalan
4. Lihat log real-time di console

### Menghentikan Bot

Klik tombol **"Stop"** pada bot yang sedang berjalan.

### Menghapus Bot

Klik tombol **"Hapus"** (merah) untuk menghapus bot permanen.

## 📁 Struktur Project

```
project-panel/
├── config/
│   ├── database.js        # Koneksi PostgreSQL
│   └── init-db.js         # Inisialisasi schema
├── middleware/
│   └── auth.js            # JWT authentication
├── routes/
│   ├── auth.js            # Login/Register/Verify
│   ├── admin.js           # Admin routes
│   ├── forgotPassword.js  # Forgot password flow
│   └── monitoring.js      # Monitoring endpoints
├── services/
│   └── telegramBot.js     # Official bot handler
├── templates/             # Template bot siap pakai
│   ├── group_manager_bot/
│   ├── auto_response_bot/
│   ├── utility_tools_bot/
│   ├── echo_bot/
│   ├── calculator_bot/
│   ├── info_bot/
│   └── welcome_bot/
├── bots/                  # Folder bot yang dibuat user (auto-generated)
├── public/                # Frontend files
│   ├── index.html         # Login page
│   ├── register.html      # Registration page
│   ├── forgot-password.html
│   ├── dashboard.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── auth.js
│       ├── dashboard.js
│       └── forgot-password.js
├── server.js              # Main Express server
├── package.json
├── .env                   # Environment variables (JANGAN COMMIT!)
├── .env.example           # Example env file
├── .gitignore
├── RESET_DATABASE.sql     # Script reset database
└── README.md              # Dokumentasi ini
```

## 🔧 API Endpoints

### Public Routes
- `POST /api/auth/register` - Daftar akun baru
- `POST /api/auth/verify` - Verifikasi kode registrasi
- `POST /api/auth/resend-code` - Kirim ulang kode
- `POST /api/auth/login` - Login
- `POST /api/forgot-password-request` - Request reset code
- `POST /api/forgot-password-verify` - Verify reset code
- `POST /api/forgot-password-reset` - Reset password

### Protected Routes (Butuh Token)
- `GET /api/templates` - Daftar template bot
- `GET /api/bots` - Daftar bot milik user
- `POST /api/bots` - Buat bot baru
- `POST /api/bots/:id/toggle` - Start/Stop bot
- `DELETE /api/bots/:id` - Hapus bot
- `GET /api/auth/me` - Data user yang login
- `GET /api/auth/profile` - Profil lengkap user
- `POST /api/auth/change-password` - Ubah password
- `POST /api/auth/update-username` - Update username

## 🔒 Keamanan

- Password di-hash dengan bcrypt (10 rounds)
- JWT token expired dalam 7 hari
- Rate limiting pada endpoint sensitif
- Input validation di semua form
- SQL injection prevention (parameterized queries)
- XSS prevention (HTML escaping)
- SSL required untuk koneksi database

## 🆘 Troubleshooting

### Error: "connect ECONNREFUSED ::1:5432"
**Solusi**: Pastikan DATABASE_URL di `.env` sudah benar dengan URL dari Neon.

### Error: "column description of relation bots does not exist"
**Solusi**: Jalankan script `RESET_DATABASE.sql` di Neon Dashboard.

### Error: "ara is not defined"
**Solusi**: Sudah diperbaiki di `dashboard.js`. Refresh browser dengan Ctrl+F5.

### Bot tidak start
**Solusi**: 
- Pastikan token valid dari @BotFather
- Cek log error di dashboard
- Pastikan Python terinstall: `python --version`
- Install dependencies: `pip install python-telegram-bot==21.0`

### Kode verifikasi tidak sampai
**Solusi**:
- Pastikan sudah chat bot official dulu
- Cek spam folder di Telegram
- Pastikan OFFICIAL_BOT_TOKEN benar

### "Terlalu banyak percobaan"
**Solusi**: Tunggu 10-15 menit atau restart server untuk reset rate limiter.

## 🛠️ Development

### Menambah Template Bot Baru

1. Buat folder di `templates/nama_template/`
2. Buat file `bot.py` dengan struktur:
   ```python
   import os
   from telegram import Update
   from telegram.ext import Application, CommandHandler
   
   TOKEN = os.getenv('BOT_TOKEN')
   BOT_ID = os.getenv('BOT_ID', 'Unknown')
   
   async def start(update: Update, context):
       await update.message.reply_text('Halo!')
   
   def main():
       app = Application.builder().token(TOKEN).build()
       app.add_handler(CommandHandler("start", start))
       app.run_polling()
   
   if __name__ == '__main__':
       main()
   ```
3. Buat `info.json`:
   ```json
   {
       "name": "Nama Template",
       "description": "Deskripsi template",
       "icon": "🤖",
       "commands": ["/start", "/help"]
   }
   ```
4. Buat `requirements.txt` jika perlu dependencies tambahan
5. Restart server

### Running in Production

```bash
# Set NODE_ENV=production
# Gunakan PM2 atau systemd
npm install -g pm2
pm2 start server.js --name bot-panel
pm2 save
pm2 startup
```

## 📝 License

MIT License - bebas digunakan untuk personal dan commercial.

## 🤝 Kontribusi

Kontribusi sangat欢迎! Silakan buat issue atau pull request untuk fitur baru atau bug fix.

---

**Dibuat dengan ❤️ untuk komunitas Telegram Bot Indonesia**
