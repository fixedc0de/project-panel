"""
Utility Tools Bot - Template Bot Telegram dengan berbagai fitur utilitas
"""

import os
import sys
import sqlite3
import random
import math
from datetime import datetime, timedelta
import logging

logging.basicConfig(format='%(asctime)s [%(name)s] %(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    logger.info("Installing python-telegram-bot...")
    os.system("pip install python-telegram-bot==21.0")
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes


class UtilityDB:
    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        db_path = os.path.join(os.path.dirname(__file__), f'{bot_id}.db')
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.init_db()
    
    def init_db(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            remind_at TIMESTAMP NOT NULL
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            quote TEXT NOT NULL,
            author TEXT,
            category TEXT DEFAULT 'personal'
        )''')
        self.conn.commit()
    
    def add_reminder(self, user_id: int, message: str, remind_at: datetime):
        self.cursor.execute('INSERT INTO reminders (user_id, message, remind_at) VALUES (?, ?, ?)',
                          (user_id, message, remind_at))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_reminders(self, user_id: int) -> list:
        self.cursor.execute('SELECT id, message, remind_at FROM reminders WHERE user_id = ?', (user_id,))
        return self.cursor.fetchall()
    
    def delete_reminder(self, reminder_id: int):
        self.cursor.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
        self.conn.commit()
    
    def add_note(self, user_id: int, title: str, content: str):
        self.cursor.execute('INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)',
                          (user_id, title, content))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_notes(self, user_id: int) -> list:
        self.cursor.execute('SELECT id, title, content FROM notes WHERE user_id = ?', (user_id,))
        return self.cursor.fetchall()
    
    def delete_note(self, note_id: int):
        self.cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
        self.conn.commit()
    
    def save_quote(self, user_id: int, quote: str, author: str, category: str):
        self.cursor.execute('INSERT INTO quotes (user_id, quote, author, category) VALUES (?, ?, ?, ?)',
                          (user_id, quote, author, category))
        self.conn.commit()
    
    def get_quotes(self, user_id: int, category: str = None) -> list:
        if category:
            self.cursor.execute('SELECT quote, author FROM quotes WHERE user_id = ? AND category = ?', (user_id, category))
        else:
            self.cursor.execute('SELECT quote, author FROM quotes WHERE user_id = ?', (user_id,))
        return self.cursor.fetchall()


QUOTES = {
    "motivasi": [
        ("Kesuksesan adalah jumlah dari usaha kecil yang diulang setiap hari.", "Robert Collier"),
        ("Jangan berhenti ketika lelah, berhentilah ketika selesai.", "Unknown"),
        ("Mimpi tidak menjadi kenyataan melalui sihir; itu membutuhkan keringat, tekad dan kerja keras.", "Colin Powell"),
    ],
    "cinta": [
        ("Cinta bukan tentang menemukan seseorang yang sempurna, tapi melihat seseorang dengan cara yang sempurna.", "Sam Keen"),
        ("Di mana ada cinta, di situ ada kehidupan.", "Mahatma Gandhi"),
    ],
    "sukses": [
        ("Sukses adalah berjalan dari kegagalan ke kegagalan tanpa kehilangan antusiasme.", "Winston Churchill"),
        ("Kesempatan tidak terjadi, Anda menciptakannya.", "Chris Grosser"),
    ]
}


class UtilityToolsBot:
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        self.bot_id = os.getenv('BOT_ID', 'utility_tools')
        if not self.token:
            print("ERROR: BOT_TOKEN tidak ditemukan!")
            sys.exit(1)
        
        self.db = UtilityDB(self.bot_id)
        self.app = Application.builder().token(self.token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("calc", self.cmd_calc))
        self.app.add_handler(CommandHandler("quote", self.cmd_quote))
        self.app.add_handler(CommandHandler("savequote", self.cmd_savequote))
        self.app.add_handler(CommandHandler("myquotes", self.cmd_myquotes))
        self.app.add_handler(CommandHandler("remind", self.cmd_remind))
        self.app.add_handler(CommandHandler("myreminders", self.cmd_myreminders))
        self.app.add_handler(CommandHandler("note", self.cmd_note))
        self.app.add_handler(CommandHandler("mynotes", self.cmd_mynotes))
        self.app.add_handler(CommandHandler("random", self.cmd_random))
        self.app.add_handler(CommandHandler("coin", self.cmd_coin))
        self.app.add_handler(CommandHandler("dice", self.cmd_dice))
        self.app.add_handler(CommandHandler("decide", self.cmd_decide))
        self.app.add_handler(CommandHandler("convert", self.cmd_convert))
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("👋 Halo! Saya Utility Tools Bot.\nGunakan /help untuk melihat fitur.")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("""
🛠️ **UTILITY COMMANDS:**

🧮 **Kalkulator:**
/calc <ekspresi> - Hitung matematika

💭 **Quotes:**
/quote [kategori] - Quote random
/savequote <quote> | <author> - Simpan quote
/myquotes - Lihat quote tersimpan

⏰ **Reminder:**
/remind <menit> <pesan> - Set reminder
/myreminders - Lihat reminder

📝 **Notes:**
/note <judul> <isi> - Buat catatan
/mynotes - Lihat catatan

🎲 **Random:**
/random [max] - Angka random
/coin - Lempar koin
/dice - Dadu
/decide <opsi1|opsi2> - Putuskan

🔄 **Converter:**
/convert <nilai> <dari> <ke>
Contoh: /convert 10 km mi
""")
    
    async def cmd_calc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Gunakan: /calc <ekspresi>\nContoh: /calc 2 + 2 * 3")
            return
        
        expr = ' '.join(context.args)
        try:
            # Safe eval dengan batasan
            allowed = set("0123456789+-*/.() ")
            if not all(c in allowed for c in expr):
                raise ValueError("Karakter tidak valid")
            result = eval(expr)
            await update.message.reply_text(f"🧮 Hasil: {result}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_quote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        category = context.args[0].lower() if context.args else "motivasi"
        quotes = QUOTES.get(category, QUOTES["motivasi"])
        q, a = random.choice(quotes)
        await update.message.reply_text(f"💭 \"{q}\"\n— {a}")
    
    async def cmd_savequote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or '|' not in ' '.join(context.args):
            await update.message.reply_text("Gunakan: /savequote <quote> | <author>")
            return
        
        parts = ' '.join(context.args).split('|')
        quote, author = parts[0].strip(), parts[1].strip() if len(parts) > 1 else "Unknown"
        self.db.save_quote(update.effective_user.id, quote, author, "personal")
        await update.message.reply_text("✅ Quote disimpan!")
    
    async def cmd_myquotes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        quotes = self.db.get_quotes(update.effective_user.id)
        if not quotes:
            await update.message.reply_text("Belum ada quote tersimpan.")
            return
        msg = "\n\n".join([f"\"{q}\" — {a}" for q, a in quotes[:5]])
        await update.message.reply_text(f"📚 Quotes Anda:\n{msg}")
    
    async def cmd_remind(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Gunakan: /remind <menit> <pesan>")
            return
        
        try:
            minutes = int(context.args[0])
            message = ' '.join(context.args[1:])
            remind_at = datetime.now() + timedelta(minutes=minutes)
            self.db.add_reminder(update.effective_user.id, message, remind_at)
            await update.message.reply_text(f"⏰ Reminder diatur dalam {minutes} menit!")
        except ValueError:
            await update.message.reply_text("Menit harus angka!")
    
    async def cmd_myreminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        reminders = self.db.get_reminders(update.effective_user.id)
        if not reminders:
            await update.message.reply_text("Tidak ada reminder.")
            return
        msg = "\n".join([f"{r[0]}. {r[1]} (at {r[2]})" for r in reminders])
        await update.message.reply_text(f"⏰ Reminders:\n{msg}")
    
    async def cmd_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Gunakan: /note <judul> <isi>")
            return
        
        title = context.args[0]
        content = ' '.join(context.args[1:])
        self.db.add_note(update.effective_user.id, title, content)
        await update.message.reply_text(f"✅ Catatan '{title}' disimpan!")
    
    async def cmd_mynotes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        notes = self.db.get_notes(update.effective_user.id)
        if not notes:
            await update.message.reply_text("Tidak ada catatan.")
            return
        msg = "\n".join([f"{n[0]}. **{n[1]}**" for n in notes[:10]])
        await update.message.reply_text(f"📝 Notes:\n{msg}")
    
    async def cmd_random(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        max_val = int(context.args[0]) if context.args else 100
        await update.message.reply_text(f"🎲 Angka random: {random.randint(1, max_val)}")
    
    async def cmd_coin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = "Kepala" if random.random() < 0.5 else "Ekor"
        await update.message.reply_text(f"🪙 Koin: {result}")
    
    async def cmd_dice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"🎲 Dadu: {random.randint(1, 6)}")
    
    async def cmd_decide(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Gunakan: /decide <opsi1|opsi2|...>")
            return
        options = ' '.join(context.args).split('|')
        await update.message.reply_text(f"🤔 Saya memilih: {random.choice(options)}")
    
    async def cmd_convert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) < 3:
            await update.message.reply_text("Gunakan: /convert <nilai> <dari> <ke>")
            return
        
        try:
            value = float(context.args[0])
            from_unit = context.args[1].lower()
            to_unit = context.args[2].lower()
            
            conversions = {
                ('km', 'mi'): lambda x: x * 0.621371,
                ('mi', 'km'): lambda x: x / 0.621371,
                ('kg', 'lbs'): lambda x: x * 2.20462,
                ('lbs', 'kg'): lambda x: x / 2.20462,
                ('c', 'f'): lambda x: x * 9/5 + 32,
                ('f', 'c'): lambda x: (x - 32) * 5/9,
            }
            
            result = conversions.get((from_unit, to_unit))(value)
            await update.message.reply_text(f"🔄 {value} {from_unit} = {result:.2f} {to_unit}")
        except KeyError:
            await update.message.reply_text("Unit tidak didukung!")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
    
    def run(self):
        print(f"[{self.bot_id}] Utility Tools Bot running!")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    UtilityToolsBot().run()
