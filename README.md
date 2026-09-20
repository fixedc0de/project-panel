# 🤖 Bot Panel - Platform Manajemen Telegram Bot

Panel berbasis web untuk membuat dan mengelola multiple Telegram bot secara otomatis.

## ✨ Fitur

- 🔐 **Autentikasi JWT** dengan verifikasi via Telegram
- 👤 **Sistem User** dengan role (user/admin)
- 🤖 **Multi-Bot Support** - Buat unlimited bot dari template
- 📦 **Template Bot** - Echo, Calculator, Info, Welcome bot
- 📊 **Real-time Monitoring** - CPU, Memory, Uptime per bot
- 🔌 **Socket.IO** - Log output bot secara real-time
- 🛡️ **Rate Limiting** - Proteksi terhadap brute-force
- 🔑 **Forgot Password** - Reset password via Telegram
- 👨‍💼 **Admin Dashboard** - Manage user & bot global

## 📋 Prerequisites

- Node.js >= 18.x
- Python >= 3.8
- PostgreSQL database
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
DATABASE_URL=postgresql://user:password@localhost:5432/bot_panel_db
JWT_SECRET=your-random-secret-key-here
OFFICIAL_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
PORT=3000
NODE_ENV=development
```

### 4. Setup Database
Database akan otomatis dibuat saat pertama kali server dijalankan.

### 5. Jalankan Server
```bash
node server.js
```

Server akan berjalan di `http://localhost:3000`

## 📁 Struktur Project

```
project-panel/
├── config/
│   ├── database.js       # PostgreSQL connection
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
├── templates/
│   ├── echo_bot/         # Template: Echo messages
│   ├── calculator_bot/   # Template: Math calculator
│   ├── info_bot/         # Template: User info
│   └── welcome_bot/      # Template: Group welcome
├── server.js             # Main Express server
├── package.json
└── .env.example
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
- Pilih template (Echo, Calculator, dll)
- Beri nama bot (hanya huruf kecil, angka, underscore)
- Masukkan token bot Telegram (dari @BotFather)
- Klik "Create"

### 3. Jalankan Bot
- Klik tombol "Start" pada bot yang dibuat
- Monitor log secara real-time via Socket.IO

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
    "commands": ["/start", "/help"]
}
```
4. Tambahkan `requirements.txt` jika perlu

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `JWT_SECRET` | ✅ | Secret key untuk JWT |
| `OFFICIAL_BOT_TOKEN` | ✅ | Token bot Telegram utama |
| `PORT` | ❌ | Port server (default: 3000) |
| `NODE_ENV` | ❌ | Environment (development/production) |

## 📝 Catatan Penting

- Bot user dijalankan sebagai child process Python
- Setiap bot terisolasi dalam folder terpisah
- Token bot disimpan encrypted di database
- Admin dapat ban user dan force stop bot

## 📄 License

ISC

## 👥 Author

Developed with ❤️ for Telegram Bot Management
