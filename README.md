# 🤖 Bot Panel - Platform Manajemen Bot Telegram

Panel kontrol berbasis web untuk mengelola multiple bot Telegram dengan mudah. Dibangun dengan Node.js (Express) backend dan frontend vanilla JavaScript, mendukung berbagai template bot siap pakai.

## ✨ Fitur Utama

### 🔐 Sistem Autentikasi
- Register & Login dengan JWT
- Forgot Password dengan email reset link
- Session management dengan localStorage
- Role-based access control

### 🤖 Multi-Bot Management
- Buat unlimited bot dari satu dashboard
- Support 7+ template bot berbeda
- Start/Stop bot secara individual
- Real-time monitoring status bot
- Log output bot via Socket.IO

### 📦 Template Bot Tersedia

#### 1. **Group Manager Bot** 🛡️
Bot manajemen grup lengkap dengan fitur moderasi.
- Welcome & goodbye messages
- Warn system (kick/ban setelah 3 warn)
- Mute/unmute members
- Anti-link detector
- Custom commands per grup
- Statistics tracking

**Commands:** `/start`, `/help`, `/setwelcome`, `/warn`, `/warnings`, `/kick`, `/ban`, `/mute`, `/unmute`, `/addcmd`, `/stats`

#### 2. **Auto Response Bot** 💬
Bot auto-response cerdas dengan pattern matching.
- Exact keyword matching
- Regex pattern support
- Capture groups
- Response statistics
- Easy management via commands

**Commands:** `/start`, `/help`, `/addresponse`, `/delresponse`, `/listresponse`, `/stats`

#### 3. **Utility Tools Bot** 🛠️
Kumpulan tools berguna dalam satu bot.
- Scientific calculator
- Quote generator & saver
- Reminder & timer
- Personal notes
- Unit converter
- Random tools (coin flip, dice, decision maker)

**Commands:** `/calc`, `/quote`, `/savequote`, `/remind`, `/note`, `/random`, `/coin`, `/dice`, `/decide`, `/convert`

#### 4. **Echo Bot** 🔁
Bot sederhana yang mengulang pesan user.

#### 5. **Calculator Bot** 🧮
Bot khusus untuk perhitungan matematika.

#### 6. **Info Bot** 📊
Bot yang menampilkan informasi sistem dan statistik.

#### 7. **Welcome Bot** 🎉
Bot khusus welcome message dengan custom text.

### 💾 Database
- **PostgreSQL (Neon)** untuk data panel (users, bots config)
- **SQLite** untuk data per-bot (setiap bot punya database sendiri)
- Isolasi data antar bot untuk keamanan dan skalabilitas

## 🚀 Instalasi

### Prerequisites
- Node.js >= 14.x
- Python >= 3.8
- PostgreSQL account (Neon recommended)
- Telegram Bot Token dari [@BotFather](https://t.me/BotFather)

### Langkah-langkah

1. **Clone repository**
```bash
git clone <repository-url>
cd project-panel
```

2. **Install dependencies**
```bash
npm install
```

3. **Setup environment variables**

Copy file `.env.example` ke `.env`:
```bash
cp .env.example .env
```

Edit `.env` dengan konfigurasi Anda:
```env
# Server
PORT=3000
NODE_ENV=development

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@ep-xxx-xxx.region.aws.neon.tech/dbname?sslmode=require

# JWT Secret (generate random string)
JWT_SECRET=your-super-secret-jwt-key-min-32-chars

# Official Bot Token (untuk notifikasi panel)
OFFICIAL_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**Cara mendapatkan DATABASE_URL dari Neon:**
1. Login ke [console.neon.tech](https://console.neon.tech)
2. Pilih project Anda
3. Klik "Connection Details"
4. Copy connection string (pastikan ada `?sslmode=require`)

4. **Inisialisasi database**
Database akan otomatis terinisialisasi saat pertama kali server dijalankan.

5. **Jalankan server**
```bash
npm start
```

Server akan berjalan di `http://localhost:3000`

## 📁 Struktur Project

```
project-panel/
├── config/
│   ├── database.js          # Koneksi PostgreSQL
│   └── init-db.js           # Inisialisasi tabel database
├── middleware/
│   └── auth.js              # JWT authentication middleware
├── routes/
│   ├── auth.js              # Login, register, forgot password
│   ├── admin.js             # Admin routes
│   ├── forgotPassword.js    # Reset password flow
│   └── monitoring.js        # System monitoring
├── services/
│   └── telegramBot.js       # Official bot service
├── templates/               # Template bot siap pakai
│   ├── group_manager_bot/
│   │   ├── bot.py           # Main bot script
│   │   ├── requirements.txt # Python dependencies
│   │   └── info.json        # Bot metadata
│   ├── auto_response_bot/
│   ├── utility_tools_bot/
│   ├── echo_bot/
│   ├── calculator_bot/
│   ├── info_bot/
│   └── welcome_bot/
├── bots/                    # Folder bot user (auto-generated)
├── public/                  # Frontend files
│   ├── index.html           # Login page
│   ├── register.html        # Register page
│   ├── forgot-password.html # Forgot password page
│   ├── dashboard.html       # Main dashboard
│   ├── css/
│   │   └── style.css        # Stylesheet
│   └── js/
│       ├── auth.js          # Auth logic
│       └── dashboard.js     # Dashboard logic
├── server.js                # Main Express server
├── package.json
├── .env.example
├── .gitignore
└── README.md
```

## 📚 Cara Menggunakan

### 1. Register Akun
- Buka `http://localhost:3000/register.html`
- Isi username, email, dan password
- Klik "Daftar"

### 2. Login
- Buka `http://localhost:3000`
- Masukkan email dan password
- Anda akan diarahkan ke dashboard

### 3. Membuat Bot Baru
1. Di dashboard, klik "+ Tambah Bot"
2. Isi nama bot (akan jadi identifier unik)
3. Masukkan bot token dari @BotFather
4. Pilih template yang diinginkan
5. Tambahkan deskripsi (opsional)
6. Klik "Buat Bot"

### 4. Menjalankan Bot
1. Di dashboard, cari bot yang baru dibuat
2. Klik tombol "Start" pada bot card
3. Bot akan mulai berjalan
4. Status berubah menjadi "Aktif" (hijau)

### 5. Menghentikan Bot
- Klik tombol "Stop" pada bot card yang sedang aktif

### 6. Menghapus Bot
- Klik tombol "Hapus" (merah) pada bot card
- Konfirmasi penghapusan
- Bot akan dihentikan (jika berjalan) dan dihapus dari database

## 🔧 Development

### Menambah Template Bot Baru

1. Buat folder baru di `templates/<nama_template>`
2. Buat file berikut:

**bot.py** - Script utama bot:
```python
import os
import sqlite3
import telebot

BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_ID = os.getenv('BOT_ID')
DB_PATH = os.path.join(os.path.dirname(__file__), f'{BOT_ID}.db')

bot = telebot.TeleBot(BOT_TOKEN)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, user_id INTEGER, username TEXT)''')
    conn.commit()
    conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Halo! Saya bot baru.')

if __name__ == '__main__':
    init_db()
    bot.infinity_polling()
```

**requirements.txt** - Dependencies Python:
```
pyTelegramBotAPI==4.10.0
```

**info.json** - Metadata bot:
```json
{
  "name": "Nama Bot",
  "description": "Deskripsi bot",
  "icon": "🤖",
  "commands": ["/start", "/help"]
}
```

3. Restart server untuk melihat template baru

### Modifikasi Frontend

File frontend ada di folder `public/`. Edit sesuai kebutuhan:
- HTML: `*.html` files
- CSS: `public/css/style.css`
- JavaScript: `public/js/*.js`

## 🆘 Troubleshooting

### Error: ECONNREFUSED ::1:5432
**Solusi:** Pastikan `DATABASE_URL` di `.env` sudah benar dan mengarah ke Neon PostgreSQL dengan `?sslmode=require`.

### Error: ModuleNotFoundError (Python)
**Solusi:** Install dependencies di folder template bot:
```bash
cd templates/<nama_bot>
pip install -r requirements.txt
```

### Bot tidak merespon
**Solusi:**
1. Cek token bot di @BotFather
2. Pastikan bot sudah di-invite ke grup (jika bot grup)
3. Cek log di dashboard untuk error message
4. Restart bot dengan tombol Stop → Start

### Frontend 404 Not Found
**Solusi:** Pastikan folder `public/` ada dan berisi file HTML. Server sudah dikonfigurasi untuk serve static files dari folder ini.

### Login/Register tidak berfungsi
**Solusi:**
1. Cek koneksi database
2. Pastikan tabel `users` sudah terbuat
3. Periksa console browser untuk error JavaScript

## 🔒 Keamanan

- Password di-hash dengan bcrypt
- JWT token dengan expiry time
- Input validation di backend
- SQL injection prevention dengan parameterized queries
- XSS prevention dengan HTML escaping
- CORS configured

## 📝 API Endpoints

### Public Routes
- `POST /api/auth/register` - Register user baru
- `POST /api/auth/login` - Login user
- `POST /api/auth/forgot-password` - Request reset password

### Protected Routes (butuh JWT token)
- `GET /api/bots` - Daftar semua bot user
- `POST /api/bots` - Buat bot baru
- `POST /api/bots/:id/toggle` - Start/Stop bot
- `DELETE /api/bots/:id` - Hapus bot
- `GET /api/templates` - Daftar template tersedia

## 🛣️ Roadmap

- [ ] Multi-level user (Admin, Reseller, User)
- [ ] Payment gateway integration
- [ ] Transaction history
- [ ] Real-time notifications
- [ ] Queue system (Redis + BullMQ)
- [ ] Auto-restart bot on crash
- [ ] Webhook support
- [ ] REST API documentation (Swagger)
- [ ] Docker support
- [ ] CI/CD pipeline

## 📄 License

MIT License - feel free to use for personal or commercial projects.

## 👥 Contributing

Kontribusi sangat diterima! Silakan buat pull request atau issue untuk fitur baru, bug fix, atau improvement.

---

**Dibuat dengan ❤️ untuk komunitas Telegram Bot Indonesia**
