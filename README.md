# 🤖 Bot Panel - Platform Manajemen Telegram Bot

Panel berbasis web untuk membuat dan mengelola multiple Telegram bot secara otomatis dengan berbagai template bot siap pakai.

## ✨ Fitur Utama

- 🔐 **Autentikasi JWT** dengan verifikasi via Telegram
- 👤 **Sistem User** dengan role (user/admin)
- 🤖 **Multi-Bot Support** - Buat unlimited bot dari template
- 📦 **Template Bot Lengkap**:
  - 🛡️ **Group Manager** - Moderasi grup, welcome message, warn/kick/ban
  - 💬 **Auto Response** - Auto-reply berdasarkan keyword & regex
  - 🛠️ **Utility Tools** - Kalkulator, quotes, reminder, notes, converter
  - 🔁 **Echo Bot** - Bot sederhana untuk testing
  - 📊 **Info Bot** - Menampilkan informasi user
  - 🎉 **Welcome Bot** - Welcome message untuk grup
- 📊 **Real-time Monitoring** - CPU, Memory, Uptime per bot
- 🔌 **Socket.IO** - Log output bot secara real-time
- 🛡️ **Rate Limiting** - Proteksi terhadap brute-force
- 🔑 **Forgot Password** - Reset password via Telegram
- 👨‍💼 **Admin Dashboard** - Manage user & bot global
- 💾 **Database SQLite Per Bot** - Setiap bot memiliki database sendiri

## 📋 Prerequisites

- Node.js >= 18.x
- Python >= 3.8
- PostgreSQL database (Neon, Supabase, atau local)
- Telegram Bot Token (untuk official bot)

## 🚀 Instalasi

### 1. Clone Repository
```bash
git clone <repository-url>
cd project-panel
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Setup Environment
Copy `.env.example` ke `.env` dan sesuaikan:
```bash
cp .env.example .env
```

Edit `.env`:
```env
# Untuk Neon PostgreSQL (cloud)
DATABASE_URL=postgresql://user:password@ep-xxx-xxx.us-east-2.aws.neon.tech/bot_panel?sslmode=require

# Atau untuk local PostgreSQL
# DATABASE_URL=postgresql://postgres:password@localhost:5432/bot_panel_db

JWT_SECRET=your-random-secret-key-here
OFFICIAL_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
PORT=3000
NODE_ENV=development
```

**Cara mendapatkan DATABASE_URL dari Neon:**
1. Buka https://console.neon.tech
2. Pilih project Anda
3. Klik "Connection Details"
4. Copy connection string dan tambahkan `?sslmode=require`

**Cara mendapatkan OFFICIAL_BOT_TOKEN:**
1. Buka Telegram, cari @BotFather
2. Kirim `/newbot`
3. Ikuti instruksi untuk membuat bot
4. Copy token yang diberikan

### 4. Setup Database
Database akan otomatis dibuat saat pertama kali server dijalankan. Tabel yang dibuat:
- `users` - Data pengguna
- `verification_codes` - Kode verifikasi registrasi
- `bots` - Daftar bot user
- `password_resets` - Kode reset password

### 5. Jalankan Server
```bash
npm start
```

Server akan berjalan di `http://localhost:3000`

## 📁 Struktur Project

```
project-panel/
├── config/
│   ├── database.js       # PostgreSQL connection (Neon compatible)
│   └── init-db.js        # Auto create tables
├── middleware/
│   └── auth.js           # JWT authentication
├── routes/
│   ├── auth.js           # Login, register, verify
│   ├── admin.js          # Admin endpoints
│   ├── forgotPassword.js # Reset password flow
│   └── monitoring.js     # Bot stats & monitoring
├── services/
│   └── telegramBot.js    # Official bot service
├── templates/            # Template bot siap pakai
│   ├── group_manager_bot/    # 🛡️ Group moderation
│   ├── auto_response_bot/    # 💬 Auto-reply
│   ├── utility_tools_bot/    # 🛠️ Utility commands
│   ├── echo_bot/             # 🔁 Simple echo
│   ├── calculator_bot/       # 🧮 Calculator
│   ├── info_bot/             # 📊 User info
│   └── welcome_bot/          # 🎉 Welcome message
├── bot_templates/        # Template tambahan (advanced)
│   ├── group_manager/
│   ├── auto_response/
│   └── utility_tools/
├── server.js             # Main Express server
├── package.json
├── .env.example          # Template environment variables
└── README.md
```

## 🔧 API Endpoints

### Public Routes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Daftar user baru |
| POST | `/api/auth/verify` | Verifikasi kode |
| POST | `/api/auth/login` | Login user |
| POST | `/api/forgot-password/request-code` | Minta kode reset |
| POST | `/api/forgot-password/reset-password` | Reset password |

### Protected Routes (Butuh Token)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/templates` | List template bot |
| GET | `/api/bots` | List bot milik user |
| POST | `/api/bots/create` | Buat bot baru |
| POST | `/api/bots/:id/start` | Start bot |
| POST | `/api/bots/:id/stop` | Stop bot |
| DELETE | `/api/bots/:id` | Hapus bot |
| GET | `/api/monitoring/my-bots` | Stats bot user |

### Admin Routes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/stats` | System statistics |
| GET | `/api/admin/users` | List semua user |
| POST | `/api/admin/users/:id/toggle-ban` | Ban/unban user |
| GET | `/api/admin/bots` | List semua bot |
| POST | `/api/admin/bots/:name/force-stop` | Force stop bot |

## 🤖 Cara Menggunakan

### 1. Daftar Akun
- Kirim `/start` ke official bot Telegram Anda
- Dapatkan Telegram ID Anda (bisa pakai @userinfobot)
- Register di panel dengan Telegram ID tersebut
- Masukkan kode verifikasi yang dikirim bot

### 2. Buat Bot
- Login ke panel
- Pilih template:
  - **Group Manager** - Untuk moderasi grup
  - **Auto Response** - Untuk FAQ otomatis
  - **Utility Tools** - Untuk berbagai utilitas
  - **Echo Bot** - Untuk testing
- Beri nama bot (hanya huruf kecil, angka, underscore)
- Masukkan token bot Telegram (dari @BotFather)
- Klik "Create"

### 3. Jalankan Bot
- Klik tombol "Start" pada bot yang dibuat
- Monitor log secara real-time via Socket.IO
- Tambahkan bot ke grup Anda (untuk Group Manager)

## 📚 Template Bot Detail

### 1. Group Manager Bot (🛡️)
Bot untuk manajemen grup Telegram dengan fitur:
- Welcome & goodbye messages
- Moderasi: /warn, /kick, /ban, /mute
- Warning system (auto-kick setelah 3 warnings)
- Custom commands per grup
- Statistik grup

**Commands:** `/start`, `/help`, `/setwelcome`, `/warn`, `/warnings`, `/kick`, `/ban`, `/mute`, `/unmute`, `/addcmd`, `/stats`

### 2. Auto Response Bot (💬)
Bot auto-response berdasarkan keyword:
- Exact match responses
- Regex pattern support
- Statistik trigger

**Commands:** `/start`, `/help`, `/addresponse`, `/delresponse`, `/listresponse`, `/stats`

**Contoh:**
```
/addresponse halo Hai juga!
/addpattern harga.*rp(\d+) | Harga adalah Rp{1}
```

### 3. Utility Tools Bot (🛠️)
Bot serbaguna dengan banyak fitur:
- 🧮 Kalkulator ilmiah
- 💭 Quote generator
- ⏰ Reminder & timer
- 📝 Catatan pribadi
- 🔄 Converter unit (km↔mi, kg↔lbs, °C↔°F)
- 🎲 Random tools (coin flip, dice, decide)

**Commands:** `/calc`, `/quote`, `/savequote`, `/remind`, `/note`, `/random`, `/coin`, `/dice`, `/decide`, `/convert`

## 🛠️ Development

### Menambah Template Baru
1. Buat folder di `templates/<nama_bot>/`
2. Tambahkan file `bot.py` (Python Telegram bot)
3. Tambahkan `info.json`:
```json
{
    "name": "My Bot",
    "description": "Deskripsi bot",
    "icon": "🚀",
    "commands": ["/start", "/help"],
    "category": "Utility",
    "version": "1.0.0"
}
```
4. Tambahkan `requirements.txt` jika perlu

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (Neon compatible) |
| `JWT_SECRET` | ✅ | Secret key untuk JWT |
| `OFFICIAL_BOT_TOKEN` | ✅ | Token bot Telegram utama |
| `PORT` | ❌ | Port server (default: 3000) |
| `NODE_ENV` | ❌ | Environment (development/production) |

## 📝 Catatan Penting

- **Database**: Gunakan Neon PostgreSQL untuk cloud database gratis dengan SSL
- **Bot Isolation**: Setiap bot user dijalankan sebagai child process Python terpisah
- **Database SQLite**: Setiap bot memiliki database SQLite sendiri di folder bot
- **Token Security**: Token bot disimpan encrypted di database
- **Admin Control**: Admin dapat ban user dan force stop bot
- **Real-time Logs**: Log bot dikirim via Socket.IO ke dashboard

## 🔒 Keamanan

- Password di-hash dengan bcrypt
- JWT token dengan expiry time
- Rate limiting untuk mencegah brute-force
- Input validation pada semua endpoint
- SSL required untuk koneksi database cloud

## 📄 License

ISC

## 👥 Author

Developed with ❤️ for Telegram Bot Management

## 🆘 Troubleshooting

### Error: connect ECONNREFUSED
Pastikan DATABASE_URL sudah benar dan database aktif. Untuk Neon, tambahkan `?sslmode=require`.

### Error: BOT_TOKEN tidak ditemukan
Pastikan token bot Telegram sudah diisi saat membuat bot di panel.

### Bot tidak merespon
1. Cek apakah bot sudah di-start di panel
2. Pastikan token bot valid
3. Cek log bot di dashboard
