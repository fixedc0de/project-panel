# 🤖 Telegram Bot Templates Collection

Kumpulan template bot Telegram yang modular, siap pakai, dan mudah dikustomisasi. Setiap bot memiliki database SQLite sendiri untuk penyimpanan data yang terisolasi.

## 📦 Template Bot Tersedia

### 1. Group Manager Bot (`/bot_templates/group_manager/`)
Bot untuk manajemen grup Telegram dengan fitur lengkap:

**Fitur:**
- ✅ Welcome & Goodbye messages (customizable)
- 🔨 Moderation: ban, kick, mute, unmute
- ⚠️ Warning system (auto-kick setelah 3 warnings)
- 🔗 Anti-link detector
- 📜 Custom rules grup
- 📝 Custom commands per grup
- 📊 Statistik grup

**Cara Menjalankan:**
```bash
cd bot_templates/group_manager
python bot.py --token YOUR_BOT_TOKEN --name MyGroupBot
```

**Perintah Admin:**
```
/warn - Beri warning ke user
/ban - Ban user dari grup
/kick - Kick user dari grup
/mute - Mute user
/setwelcome <pesan> - Set welcome message
/setrules <rules> - Set rules grup
/toggleantilink - Enable/disable anti link
/addcmd <cmd> <response> - Tambah custom command
/stats - Lihat statistik grup
```

---

### 2. Auto Response Bot (`/bot_templates/auto_response/`)
Bot yang menjawab otomatis berdasarkan keyword atau pattern regex.

**Fitur:**
- 🔑 Auto-response berdasarkan keyword
- 🎯 Smart pattern matching dengan regex
- 🔢 Support capture groups dalam response
- 📊 Statistik penggunaan keyword
- 🌍 Global dan chat-specific responses
- 🟢/🔴 Enable/disable per response

**Cara Menjalankan:**
```bash
cd bot_templates/auto_response
python bot.py --token YOUR_BOT_TOKEN --name MyAutoBot
```

**Perintah:**
```
/addresponse <keyword> <response> - Tambah auto response
/delresponse <keyword> - Hapus auto response
/listresponse - List semua auto response
/addpattern <pattern> <response> - Tambah pattern regex
/listpattern - List semua pattern
/stats - Lihat statistik
/topkeywords - Keyword paling sering dipicu
```

**Contoh Pattern Regex:**
```
/addpattern harga.*rp(\d+) | Harga yang dimasukkan adalah Rp{1} --flags=i
```

---

### 3. Utility Tools Bot (`/bot_templates/utility_tools/`)
Bot serbaguna dengan berbagai fitur utilitas untuk kehidupan sehari-hari.

**Fitur:**
- 🧮 Kalkulator ilmiah (support sin, cos, sqrt, dll)
- 💭 Quote generator (motivasi, cinta, sukses, kehidupan)
- 💾 Save favorite quotes
- ⏰ Reminder dengan notifikasi
- ⏱️ Timer countdown
- 📝 Catatan pribadi (notes)
- 🔄 Converter unit (km↔mi, kg↔lbs, °C↔°F, dll)
- 🎲 Random tools (angka random, coin flip, dice roll, decide)

**Cara Menjalankan:**
```bash
cd bot_templates/utility_tools
python bot.py --token YOUR_BOT_TOKEN --name MyUtilityBot
```

**Perintah:**
```
/calc <ekspresi> - Kalkulator
/quote [kategori] - Quote acak
/savequote <quote> | <author> - Simpan quote
/remind <menit> <pesan> - Set reminder
/timer <menit> - Set timer
/note <judul> <isi> - Buat catatan
/convert <nilai> <dari> <ke> - Convert unit
/random [max] - Angka random
/coin - Lempar koin
/dice - Lempar dadu
/decide <pilihan1|pilihan2> - Bantu putuskan
```

---

## 🏗️ Struktur Project

```
bot_templates/
├── group_manager/          # Bot manajemen grup
│   ├── bot.py             # Main bot code
│   └── databases/         # SQLite databases (auto-created)
├── auto_response/         # Bot auto response
│   ├── bot.py
│   └── databases/
├── utility_tools/         # Bot utility
│   ├── bot.py
│   └── databases/
├── requirements.txt       # Python dependencies
└── README.md             # This file

shared_libs/
└── bot_utils.py          # Shared utilities untuk semua bot
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r bot_templates/requirements.txt
```

### 2. Jalankan Bot Pilihan
```bash
# Contoh: Jalankan Group Manager Bot
python bot_templates/group_manager/bot.py --token BOT_TOKEN_HERE --name MyBot
```

### 3. Dapatkan Bot Token
1. Buka Telegram, cari @BotFather
2. Kirim `/newbot`
3. Ikuti instruksi untuk membuat bot
4. Salin token yang diberikan

---

## 📚 Shared Library (`shared_libs/bot_utils.py`)

Library bersama yang menyediakan:

- **DatabaseManager**: Class base untuk operasi SQLite
- **ModuleRegistry**: Sistem registry untuk modul bot yang modular
- **Utility Functions**: 
  - `format_duration()` - Format durasi ke string
  - `sanitize_text()` - Sanitize text untuk Telegram
  - `is_admin()` - Cek apakah user adalah admin
  - `log_action()` - Log aktivitas bot

---

## 🛠️ Membuat Bot Baru

### 1. Buat Struktur Folder
```bash
mkdir -p bot_templates/my_new_bot
```

### 2. Import Shared Library
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared_libs'))
from bot_utils import DatabaseManager, ModuleRegistry
```

### 3. Extend DatabaseManager
```python
class MyBotDB(DatabaseManager):
    def init_db(self):
        self.execute('''
            CREATE TABLE IF NOT EXISTS my_table (
                id INTEGER PRIMARY KEY,
                data TEXT
            )
        ''')
```

### 4. Register Modules (Optional)
```python
@ModuleRegistry.register('my_module')
class MyModule:
    @staticmethod
    async def handle(update, context, db):
        # Your logic here
        pass
```

### 5. Jalankan Bot
```bash
python bot_templates/my_new_bot/bot.py --token TOKEN --name MyBot
```

---

## 💡 Tips Pengembangan

1. **Database Terpisah**: Setiap bot instance punya database sendiri berdasarkan token
2. **Modular Design**: Gunakan `@ModuleRegistry.register()` untuk fitur yang bisa di-enable/disable
3. **Logging**: Selalu gunakan `log_action()` untuk tracking aktivitas
4. **Error Handling**: Wrap operasi berisiko dengan try-except
5. **Sanitize Input**: Gunakan `sanitize_text()` sebelum mengirim ke Telegram

---

## 🔐 Keamanan

- ✅ Input validation pada semua command
- ✅ Admin-only commands untuk operasi sensitif
- ✅ SQL injection prevention (parameterized queries)
- ✅ Text sanitization untuk mencegah malformed messages

---

## 📝 License

Free to use for personal and commercial projects.

---

## 🤝 Kontribusi

Silakan contribute dengan:
1. Menambahkan template bot baru
2. Memperbaiki bug
3. Menambahkan fitur ke bot yang ada
4. Meningkatkan dokumentasi

---

## 📞 Support

Jika ada pertanyaan atau masalah, silakan buat issue di repository ini.

**Happy Bot Building! 🎉**
