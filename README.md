# 🤖 Bot Panel - Platform Manajemen Bot Telegram

Platform manajemen bot Telegram berbasis web yang modern, aman, dan mudah digunakan. Kelola multiple bot Telegram Anda dari satu dashboard dengan fitur lengkap dan template bot siap pakai.

![Bot Panel](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Node.js](https://img.shields.io/badge/node-%3E%3D14-green)
![Python](https://img.shields.io/badge/python-%3E%3D3.8-blue)

---

## ✨ Fitur Utama

### 🔐 Sistem Autentikasi Modern
- **Login menggunakan Telegram ID** - Tidak perlu email, cukup gunakan Telegram ID Anda
- **Verifikasi 2 langkah via Bot Official** - Kode verifikasi dikirim langsung ke Telegram
- **Forgot Password via Telegram** - Reset password mudah melalui bot official
- **JWT Token Authentication** - Keamanan terjamin dengan token JWT
- **Rate Limiting** - Proteksi dari brute force attacks

### 🤖 Template Bot Siap Pakai (7 Templates)

#### 1. 🛡️ Group Manager Bot
Bot manajemen grup lengkap dengan fitur moderasi otomatis.
- Welcome & goodbye messages
- Auto warn, kick, ban, mute sistem
- Anti-link detector
- Custom commands per grup
- Statistik aktivitas grup

**Commands:** `/start`, `/help`, `/setwelcome`, `/warn`, `/warnings`, `/kick`, `/ban`, `/mute`, `/unmute`, `/addcmd`, `/stats`

#### 2. 💬 Auto Response Bot
Bot auto response cerdas dengan pattern matching.
- Keyword exact match
- Regex pattern support
- Capture groups
- Response statistics

**Commands:** `/start`, `/help`, `/addresponse`, `/delresponse`, `/listresponse`, `/stats`

#### 3. 🛠️ Utility Tools Bot
Kumpulan tools utility lengkap untuk berbagai kebutuhan.
- Kalkulator ilmiah
- Quote generator & saver
- Reminder & timer
- Catatan pribadi
- Unit converter
- Random tools (coin flip, dice roll, decision maker)

**Commands:** `/calc`, `/quote`, `/savequote`, `/remind`, `/note`, `/random`, `/coin`, `/dice`, `/decide`, `/convert`

#### 4. 🔁 Echo Bot
Bot sederhana untuk echo pesan.

#### 5. 🧮 Calculator Bot
Bot kalkulator dengan operasi matematika dasar.

#### 6. 📊 Info Bot
Bot untuk menampilkan informasi user dan grup.

#### 7. 🎉 Welcome Bot
Bot khusus welcome message dengan custom template.

### 📊 Dashboard Modern
- UI/UX modern dengan gradient design
- Real-time bot status monitoring
- Statistics cards (Total Bot, Bot Aktif, Total Pengguna)
- Responsive design (mobile-friendly)
- Smooth animations & transitions

### 🗄️ Database
- **PostgreSQL (Neon)** - Cloud database dengan SSL connection
- **SQLite per Bot** - Setiap bot memiliki database SQLite terpisah untuk data spesifik
- Auto migration & table creation

### 🚀 Bot Management
- Start/Stop bot dengan satu klik
- Real-time log monitoring via Socket.IO
- Bot isolation (setiap bot berjalan terpisah)
- Auto-restart on crash (opsional)

---

## 🚀 Instalasi

### Prerequisites
- Node.js >= 14.x
- Python >= 3.8
- PostgreSQL account di [Neon](https://neon.tech) (gratis)
- Telegram Bot Token dari [@BotFather](https://t.me/BotFather)

### Langkah 1: Clone Repository
```bash
git clone <repository-url>
cd project-panel
```

### Langkah 2: Install Dependencies
```bash
# Install Node.js dependencies
npm install

# Install Python dependencies (untuk setiap template bot)
pip install python-telegram-bot==20.7
pip install requests
```

### Langkah 3: Setup Environment Variables

Copy file `.env.example` ke `.env`:
```bash
cp .env.example .env
```

Edit file `.env` dengan konfigurasi Anda:

```env
# Database Configuration (Neon PostgreSQL)
# Dapatkan dari: https://console.neon.tech -> Project -> Connection Details
DATABASE_URL=postgresql://user:password@ep-xxx-xxx.us-east-2.aws.neon.tech/bot_panel?sslmode=require

# JWT Secret (generate random string)
# Generate dengan: node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production

# Official Bot Token (dari @BotFather)
OFFICIAL_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Server Port
PORT=3000

# Environment
NODE_ENV=development
```

### Langkah 4: Mendapatkan DATABASE_URL dari Neon

1. Buka [https://neon.tech](https://neon.tech) dan login
2. Buat project baru atau pilih project yang ada
3. Klik **"Connection Details"** di dashboard
4. Copy connection string yang ditampilkan
5. Pastikan ada parameter `?sslmode=require` di akhir URL
6. Paste ke file `.env` sebagai `DATABASE_URL`

Contoh DATABASE_URL:
```
postgresql://username:password@ep-cool-winter-123456.us-east-2.aws.neon.tech/botpanel?sslmode=require
```

### Langkah 5: Mendapatkan Telegram Bot Token

1. Buka Telegram dan cari [@BotFather](https://t.me/BotFather)
2. Kirim command `/newbot`
3. Ikuti instruksi untuk membuat bot
4. Simpan token yang diberikan (berformat: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Paste token ke `.env` sebagai `OFFICIAL_BOT_TOKEN`

### Langkah 6: Jalankan Server
```bash
npm start
```

Server akan berjalan di: **http://localhost:3000**

---

## 📁 Struktur Project

```
project-panel/
├── config/
│   ├── database.js          # Konfigurasi koneksi PostgreSQL
│   └── init-db.js           # Auto create tables
├── middleware/
│   └── auth.js              # JWT authentication middleware
├── routes/
│   ├── auth.js              # Login, register, verify endpoints
│   ├── admin.js             # Admin routes
│   ├── forgotPassword.js    # Forgot password flow
│   └── monitoring.js        # Monitoring endpoints
├── services/
│   └── telegramBot.js       # Official bot service
├── templates/               # Template bot siap pakai
│   ├── group_manager_bot/
│   │   ├── bot.py
│   │   ├── info.json
│   │   └── requirements.txt
│   ├── auto_response_bot/
│   ├── utility_tools_bot/
│   ├── echo_bot/
│   ├── calculator_bot/
│   ├── info_bot/
│   └── welcome_bot/
├── public/                  # Frontend files
│   ├── css/
│   │   └── style.css        # Modern gradient CSS
│   ├── js/
│   │   ├── auth.js          # Login/register logic
│   │   ├── dashboard.js     # Dashboard logic
│   │   └── forgot-password.js
│   ├── index.html           # Login page
│   ├── register.html        # Register page (2-step verification)
│   ├── forgot-password.html # Forgot password (3-step flow)
│   └── dashboard.html       # Main dashboard
├── bots/                    # Folder untuk bot yang dibuat user (auto-generated)
├── server.js                # Main Express server
├── package.json
├── .env                     # Environment variables (JANGAN commit!)
├── .env.example             # Example environment
├── .gitignore
└── README.md
```

---

## 📚 Cara Penggunaan

### 1. Registrasi Akun

1. Buka http://localhost:3000
2. Klik **"Daftar disini"**
3. Masukkan **Telegram ID** (bukan username!)
   - Cara cek Telegram ID: kirim pesan ke [@userinfobot](https://t.me/userinfobot)
4. Masukkan password (minimal 6 karakter)
5. Klik **"Daftar & Dapatkan Kode Verifikasi"**
6. Cek Telegram Anda untuk kode 6 digit dari bot official
7. Masukkan kode verifikasi
8. Akun aktif! Silakan login

### 2. Login

1. Masukkan Telegram ID dan password
2. Jika berhasil, Anda akan diarahkan ke dashboard

### 3. Membuat Bot Baru

1. Di dashboard, klik **"+ Tambah Bot"**
2. Isi form:
   - **Nama Bot**: Nama unik untuk bot Anda
   - **Bot Token**: Token dari @BotFather
   - **Template**: Pilih template bot yang diinginkan
   - **Deskripsi**: Deskripsi opsional
3. Klik **"Buat Bot"**
4. Bot akan dibuat dan siap dijalankan

### 4. Menjalankan Bot

1. Di dashboard, temukan bot yang ingin dijalankan
2. Klik tombol **"Start"** atau toggle switch
3. Bot akan mulai berjalan
4. Lihat log real-time di console atau dashboard

### 5. Menghentikan Bot

1. Klik tombol **"Stop"** pada bot yang sedang berjalan
2. Bot akan dihentikan dengan aman

### 6. Menghapus Bot

1. Klik tombol **"Hapus"** pada bot
2. Konfirmasi penghapusan
3. Bot dan semua datanya akan dihapus

---

## 🔒 Keamanan

### Fitur Keamanan yang Diterapkan:
- ✅ Password hashing dengan bcrypt (10 rounds)
- ✅ JWT token authentication (expired 7 hari)
- ✅ Rate limiting untuk mencegah brute force
- ✅ Input validation di semua endpoint
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS protection
- ✅ CORS configuration
- ✅ SSL requirement untuk database connection
- ✅ Session management yang aman

### Best Practices:
- Jangan pernah commit file `.env`
- Ganti `JWT_SECRET` dengan random string yang kuat
- Gunakan HTTPS di production
- Backup database secara berkala
- Update dependencies secara rutin

---

## 🛠️ Troubleshooting

### Error: ECONNREFUSED ::1:5432
**Solusi:** 
- Pastikan DATABASE_URL sudah benar di `.env`
- Pastikan ada `?sslmode=require` di akhir URL
- Cek koneksi internet Anda

### Error: Bot tidak bisa mengirim pesan verifikasi
**Solusi:**
- Pastikan OFFICIAL_BOT_TOKEN benar
- User harus chat bot official terlebih dahulu (klik /start)
- Cek apakah bot di-block oleh user

### Error: Module not found (Python)
**Solusi:**
```bash
pip install python-telegram-bot==20.7
pip install requests
```

### Error: Port 3000 sudah digunakan
**Solusi:**
- Ubah PORT di `.env` menjadi port lain (misal 3001)
- Atau kill process yang menggunakan port 3000

### Lupa Telegram ID
**Solusi:**
- Chat [@userinfobot](https://t.me/userinfobot) di Telegram
- Bot akan mengirimkan ID Anda

---

## 📖 API Endpoints

### Public Routes
```
POST /api/auth/register         # Registrasi akun baru
POST /api/auth/verify           # Verifikasi kode
POST /api/auth/resend-code      # Kirim ulang kode
POST /api/auth/login            # Login
POST /api/auth/forgot-password-request  # Request reset code
POST /api/auth/forgot-password-verify   # Verify reset code
POST /api/auth/forgot-password-reset    # Reset password
```

### Protected Routes (Butuh Token)
```
GET  /api/auth/me                # Get current user
GET  /api/auth/profile           # Get profile detail
POST /api/auth/change-password   # Change password
POST /api/auth/update-username   # Update username
POST /api/auth/logout            # Logout

GET  /api/templates              # List available templates
GET  /api/bots                   # List user's bots
POST /api/bots                   # Create new bot
POST /api/bots/:id/toggle        # Start/Stop bot
DELETE /api/bots/:id             # Delete bot
```

---

## 🎨 Customization

### Mengubah Tema Warna
Edit file `/public/css/style.css` di bagian `:root`:

```css
:root {
    --primary-color: #6366f1;      /* Warna utama */
    --secondary-color: #ec4899;    /* Warna sekunder */
    --bg-gradient-start: #6366f1;  /* Gradient start */
    --bg-gradient-end: #ec4899;    /* Gradient end */
}
```

### Menambah Template Bot Baru
1. Buat folder baru di `/templates/nama_bot/`
2. Buat file `bot.py` dengan logic bot Anda
3. Buat file `info.json` dengan metadata:
```json
{
    "name": "My Custom Bot",
    "description": "Deskripsi bot",
    "icon": "🤖",
    "commands": ["/start", "/help"]
}
```
4. Restart server

---

## 🚀 Deployment

### Deploy ke Production

1. **Setup Production Database**
   - Gunakan Neon production endpoint
   - Backup database secara berkala

2. **Environment Variables**
   ```env
   NODE_ENV=production
   JWT_SECRET=<strong-random-string>
   DATABASE_URL=<production-db-url>
   OFFICIAL_BOT_TOKEN=<bot-token>
   ```

3. **Install PM2 (Process Manager)**
   ```bash
   npm install -g pm2
   pm2 start server.js --name bot-panel
   pm2 save
   pm2 startup
   ```

4. **Setup HTTPS**
   - Gunakan Nginx sebagai reverse proxy
   - Dapatkan SSL certificate dari Let's Encrypt

5. **Monitoring**
   - Setup log rotation
   - Monitor resource usage
   - Setup alerts untuk downtime

---

## 📝 Changelog

### v1.0.0
- ✅ Initial release
- ✅ Telegram ID based authentication
- ✅ 7 bot templates
- ✅ Modern gradient UI
- ✅ Real-time bot monitoring
- ✅ Forgot password via Telegram
- ✅ SQLite database per bot
- ✅ Rate limiting & security features

---

## 🤝 Contributing

Kontribusi sangat diapresiasi! Silakan:
1. Fork repository
2. Buat feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

Project ini dilisensikan di bawah [MIT License](LICENSE).

---

## 👨‍💻 Developer

Dibuat dengan ❤️ untuk memudahkan manajemen bot Telegram.

**Stack Teknologi:**
- Backend: Node.js + Express.js
- Frontend: Vanilla JS + Modern CSS
- Database: PostgreSQL (Neon) + SQLite
- Bot Framework: python-telegram-bot
- Authentication: JWT
- Real-time: Socket.IO

---

## 📞 Support

Jika mengalami masalah atau punya pertanyaan:
1. Baca dokumentasi ini dengan teliti
2. Cek bagian Troubleshooting
3. Buat issue di GitHub
4. Hubungi developer

---

**Happy Bot Managing! 🚀**
