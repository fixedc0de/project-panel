"""
Bot Utility Tools - Template Bot dengan Berbagai Fitur Utilitas
Fitur: Calculator, quote generator, reminder, timer, converter, dan lain-lain
Setiap bot memiliki database SQLite sendiri
"""

import os
import sys
import math
import random
from datetime import datetime, timedelta
from typing import Optional

# Tambahkan shared_libs ke path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared_libs'))

from bot_utils import DatabaseManager, ModuleRegistry, sanitize_text, format_duration, log_action

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue
except ImportError:
    print("Installing python-telegram-bot...")
    os.system("pip install python-telegram-bot")
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue


class UtilityDB(DatabaseManager):
    """Database manager khusus untuk Utility Bot"""
    
    def init_db(self):
        """Inisialisasi tabel-tabel untuk utility bot"""
        # Tabel reminders
        self.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                message TEXT NOT NULL,
                remind_at TIMESTAMP NOT NULL,
                is_recurring INTEGER DEFAULT 0,
                recurrence_pattern TEXT,
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabel quotes favorit
        self.execute('''
            CREATE TABLE IF NOT EXISTS favorite_quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                quote TEXT NOT NULL,
                author TEXT,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabel custom converters
        self.execute('''
            CREATE TABLE IF NOT EXISTS conversion_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                from_unit TEXT NOT NULL,
                to_unit TEXT NOT NULL,
                rate REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabel notes/catatan
        self.execute('''
            CREATE TABLE IF NOT EXISTS user_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')


@ModuleRegistry.register('calculator')
class CalculatorModule:
    """Modul calculator"""
    
    @staticmethod
    def calculate(expression: str) -> str:
        """Calculate mathematical expression"""
        try:
            # Sanitize expression - hanya boleh angka dan operator
            allowed_chars = set('0123456789+-*/().^ ')
            if not all(c in allowed_chars for c in expression):
                return "❌ Ekspresi tidak valid! Hanya boleh angka dan operator (+, -, *, /, ^)"
            
            # Replace ^ dengan ** untuk power
            expression = expression.replace('^', '**')
            
            # Evaluate dengan batasan
            result = eval(expression, {"__builtins__": {}}, {
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'sqrt': math.sqrt,
                'log': math.log,
                'pi': math.pi,
                'e': math.e,
            })
            
            # Format result
            if isinstance(result, float):
                if result == int(result):
                    return str(int(result))
                return f"{result:.6f}".rstrip('0').rstrip('.')
            return str(result)
        except ZeroDivisionError:
            return "❌ Tidak bisa dibagi dengan nol!"
        except Exception as e:
            return f"❌ Error: {str(e)}"


@ModuleRegistry.register('quote')
class QuoteModule:
    """Modul quote generator"""
    
    QUOTES = [
        {"quote": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
        {"quote": "Life is what happens when you're busy making other plans.", "author": "John Lennon"},
        {"quote": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt"},
        {"quote": "Tell me and I forget. Teach me and I remember. Involve me and I learn.", "author": "Benjamin Franklin"},
        {"quote": "The best time to plant a tree was 20 years ago. The second best time is now.", "author": "Chinese Proverb"},
        {"quote": "An unexamined life is not worth living.", "author": "Socrates"},
        {"quote": "Eighty percent of success is showing up.", "author": "Woody Allen"},
        {"quote": "Your time is limited, so don't waste it living someone else's life.", "author": "Steve Jobs"},
        {"quote": "Winning isn't everything, but wanting to win is.", "author": "Vince Lombardi"},
        {"quote": "I am not a product of my circumstances. I am a product of my decisions.", "author": "Stephen Covey"},
        {"quote": "Every child is an artist. The problem is how to remain an artist once he grows up.", "author": "Pablo Picasso"},
        {"quote": "You can never cross the ocean until you have the courage to lose sight of the shore.", "author": "Christopher Columbus"},
        {"quote": "Either you run the day, or the day runs you.", "author": "Jim Rohn"},
        {"quote": "Whether you think you can or you think you can't, you're right.", "author": "Henry Ford"},
        {"quote": "The two most important days in your life are the day you are born and the day you find out why.", "author": "Mark Twain"},
    ]
    
    CATEGORIES = {
        'motivasi': ["Jangan pernah menyerah!", "Teruslah bermimpi!", "Hari ini adalah hari yang bagus!"],
        'cinta': ["Cinta adalah segalanya", "Cinta sejati takkan pernah berakhir", "Cinta mengalahkan segala"],
        'sukses': ["Sukses butuh proses", "Kerja keras mengalahkan bakat", "Fokus pada tujuan"],
        'kehidupan': ["Hidup adalah perjalanan", "Nikmati setiap momen", "Belajar dari kesalahan"],
    }
    
    @staticmethod
    def get_random_quote(category: str = None) -> dict:
        """Get random quote"""
        if category and category.lower() in QuoteModule.CATEGORIES:
            quotes = QuoteModule.CATEGORIES[category.lower()]
            return {"quote": random.choice(quotes), "author": "Anonymous"}
        return random.choice(QuoteModule.QUOTES)


class UtilityBot:
    """Main class untuk Utility Bot"""
    
    def __init__(self, token: str, bot_name: str = "UtilityBot"):
        self.token = token
        self.bot_name = bot_name
        self.db_path = os.path.join(
            os.path.dirname(__file__), 
            'databases', 
            f'{bot_name}_{token[:8]}.db'
        )
        self.db = UtilityDB(self.db_path)
        self.app = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Command /start"""
        await update.message.reply_text(
            "👋 Halo! Saya adalah Bot Utility.\n\n"
            "Saya punya banyak fitur berguna untuk membantu Anda!\n"
            "Gunakan /help untuk melihat daftar perintah."
        )
        log_action(self.bot_name, "start", update.effective_user.id)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Command /help"""
        help_text = """
📋 **DAFTAR PERINTAH UTILITY BOT**

🧮 **Calculator:**
/calc <expression> - Kalkulator ilmiah
Contoh: /calc 2+2*3 atau /calc sqrt(16)

💭 **Quotes:**
/quote [kategori] - Quote acak
Kategori: motivasi, cinta, sukses, kehidupan
/savequote - Simpan quote favorit
/myquotes - Lihat quote tersimpan

⏰ **Reminder & Timer:**
/remind <menit> <pesan> - Set reminder
/reminders - Lihat reminder aktif
/delreminder <id> - Hapus reminder
/timer <menit> - Set timer countdown

📝 **Notes:**
/note <judul> <isi> - Buat catatan
/notes - List semua catatan
/getnote <judul> - Ambil catatan
/delnote <judul> - Hapus catatan

🔄 **Converters:**
/convert <nilai> <dari> <ke> - Convert unit
Support: km-mi, kg-lbs, c-f (celcius-fahrenheit)

🎲 **Random:**
/random [max] - Angka random
/coin - Lempar koin
/dice - Lempar dadu
/decide <pilihan1|pilihan2> - Bantu putuskan

ℹ️ **Info:**
/stats - Statistik penggunaan
/about - Tentang bot
"""
        await update.message.reply_text(help_text)
    
    async def calc_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Calculator command"""
        if not context.args:
            await update.message.reply_text(
                "🧮 Gunakan: /calc <ekspresi>\n"
                "Contoh: /calc 2+2*3 atau /calc sqrt(16)"
            )
            return
        
        expression = " ".join(context.args)
        result = CalculatorModule.calculate(expression)
        
        await update.message.reply_text(f"🧮 **Result:**\n`{expression} = {result}`", parse_mode='Markdown')
        log_action(self.bot_name, "calc", update.effective_user.id, f"expr: {expression}")
    
    async def quote_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quote command"""
        category = context.args[0] if context.args else None
        quote_data = QuoteModule.get_random_quote(category)
        
        quote_text = f"""
💭 **Quote of the Day**

"{quote_data['quote']}"
— {quote_data['author']}
"""
        await update.message.reply_text(quote_text)
        log_action(self.bot_name, "quote", update.effective_user.id, f"category: {category or 'random'}")
    
    async def save_quote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save favorite quote"""
        user_id = str(update.effective_user.id)
        
        if not context.args:
            await update.message.reply_text(
                "Gunakan: /savequote <quote> | <author>\n"
                "Contoh: /savequote Hidup itu indah | Anonymous"
            )
            return
        
        text = " ".join(context.args)
        if '|' in text:
            parts = text.split('|')
            quote = parts[0].strip()
            author = parts[1].strip() if len(parts) > 1 else "Anonymous"
        else:
            quote = text
            author = "Anonymous"
        
        self.db.execute(
            "INSERT INTO favorite_quotes (user_id, quote, author) VALUES (?, ?, ?)",
            (user_id, quote, author)
        )
        
        await update.message.reply_text("✅ Quote berhasil disimpan!")
        log_action(self.bot_name, "quote_saved", update.effective_user.id)
    
    async def my_quotes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View saved quotes"""
        user_id = str(update.effective_user.id)
        quotes = self.db.fetch_all(
            "SELECT * FROM favorite_quotes WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
            (user_id,)
        )
        
        if not quotes:
            await update.message.reply_text("📝 Belum ada quote yang disimpan")
            return
        
        quote_list = "\n\n".join([
            f"💬 \"{q['quote']}\"\n— {q['author']}"
            for q in quotes
        ])
        
        await update.message.reply_text(f"📚 **My Quotes:**\n\n{quote_list}")
    
    async def remind_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set reminder"""
        user = update.effective_user
        user_id = str(user.id)
        chat_id = str(update.effective_chat.id)
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Gunakan: /remind <menit> <pesan>\n"
                "Contoh: /remind 30 Minum obat"
            )
            return
        
        try:
            minutes = int(context.args[0])
        except ValueError:
            await update.message.reply_text("⏰ Waktu harus dalam menit (angka)!")
            return
        
        message = " ".join(context.args[1:])
        remind_at = datetime.now() + timedelta(minutes=minutes)
        
        self.db.execute(
            "INSERT INTO reminders (user_id, chat_id, message, remind_at) VALUES (?, ?, ?, ?)",
            (user_id, chat_id, message, remind_at.strftime("%Y-%m-%d %H:%M:%S"))
        )
        
        await update.message.reply_text(
            f"⏰ Reminder berhasil diset!\n"
            f"📝 Pesan: {message}\n"
            f"⏱️ Waktu: {minutes} menit lagi"
        )
        
        # Schedule job
        if context.job_queue:
            context.job_queue.run_once(
                self.send_reminder,
                when=remind_at,
                data={'user_id': user_id, 'chat_id': chat_id, 'message': message}
            )
        
        log_action(self.bot_name, "reminder_set", user.id, f"in {minutes} min")
    
    async def send_reminder(self, context: ContextTypes.DEFAULT_TYPE):
        """Send reminder notification"""
        job = context.job
        data = job.data
        
        try:
            await context.bot.send_message(
                chat_id=data['chat_id'],
                text=f"⏰ **Reminder!**\n\n{data['message']}"
            )
        except Exception as e:
            print(f"Failed to send reminder: {e}")
    
    async def list_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List active reminders"""
        user_id = str(update.effective_user.id)
        
        reminders = self.db.fetch_all(
            "SELECT * FROM reminders WHERE user_id = ? AND completed = 0 ORDER BY remind_at",
            (user_id,)
        )
        
        if not reminders:
            await update.message.reply_text("⏰ Tidak ada reminder aktif")
            return
        
        reminder_list = "\n".join([
            f"{i}. [{r['remind_at']}] {r['message']}"
            for i, r in enumerate(reminders, 1)
        ])
        
        await update.message.reply_text(f"⏰ **Active Reminders:**\n\n{reminder_list}")
    
    async def timer_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set timer"""
        if not context.args:
            await update.message.reply_text(
                "Gunakan: /timer <menit>\n"
                "Contoh: /timer 5"
            )
            return
        
        try:
            minutes = int(context.args[0])
        except ValueError:
            await update.message.reply_text("⏱️ Waktu harus dalam menit (angka)!")
            return
        
        seconds = minutes * 60
        
        await update.message.reply_text(f"⏱️ Timer dimulai: {minutes} menit")
        
        if context.job_queue:
            context.job_queue.run_once(
                self.timer_done,
                when=seconds,
                data={'user_id': str(update.effective_user.id), 'chat_id': str(update.effective_chat.id), 'minutes': minutes}
            )
        
        log_action(self.bot_name, "timer_set", update.effective_user.id, f"{minutes} min")
    
    async def timer_done(self, context: ContextTypes.DEFAULT_TYPE):
        """Timer finished"""
        job = context.job
        data = job.data
        
        try:
            await context.bot.send_message(
                chat_id=data['chat_id'],
                text=f"⏱️ **Timer selesai!**\n\n{data['minutes']} menit telah berlalu."
            )
        except Exception as e:
            print(f"Failed to send timer notification: {e}")
    
    async def note_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create note"""
        user_id = str(update.effective_user.id)
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Gunakan: /note <judul> <isi>\n"
                "Contoh: /note Belanja Susu, Roti, Telur"
            )
            return
        
        title = context.args[0]
        content = " ".join(context.args[1:])
        
        self.db.execute(
            "INSERT INTO user_notes (user_id, title, content) VALUES (?, ?, ?)",
            (user_id, title, content)
        )
        
        await update.message.reply_text(f"📝 Note '{title}' berhasil dibuat!")
        log_action(self.bot_name, "note_created", update.effective_user.id, f"title: {title}")
    
    async def list_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all notes"""
        user_id = str(update.effective_user.id)
        
        notes = self.db.fetch_all(
            "SELECT title, created_at FROM user_notes WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        )
        
        if not notes:
            await update.message.reply_text("📝 Belum ada catatan")
            return
        
        note_list = "\n".join([f"📌 {n['title']} - {n['created_at']}" for n in notes])
        await update.message.reply_text(f"📚 **My Notes:**\n\n{note_list}")
    
    async def get_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get specific note"""
        user_id = str(update.effective_user.id)
        
        if not context.args:
            await update.message.reply_text("Gunakan: /getnote <judul>")
            return
        
        title = context.args[0]
        note = self.db.fetch_one(
            "SELECT * FROM user_notes WHERE user_id = ? AND title = ?",
            (user_id, title)
        )
        
        if not note:
            await update.message.reply_text(f"❌ Note '{title}' tidak ditemukan")
            return
        
        await update.message.reply_text(f"📝 **{note['title']}**\n\n{note['content']}")
    
    async def del_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete note"""
        user_id = str(update.effective_user.id)
        
        if not context.args:
            await update.message.reply_text("Gunakan: /delnote <judul>")
            return
        
        title = context.args[0]
        result = self.db.execute(
            "DELETE FROM user_notes WHERE user_id = ? AND title = ?",
            (user_id, title)
        )
        
        if result.rowcount > 0:
            await update.message.reply_text(f"✅ Note '{title}' berhasil dihapus")
        else:
            await update.message.reply_text(f"❌ Note '{title}' tidak ditemukan")
        
        log_action(self.bot_name, "note_deleted", update.effective_user.id, f"title: {title}")
    
    async def convert_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Convert units"""
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "Gunakan: /convert <nilai> <dari> <ke>\n"
                "Contoh: /convert 10 km mi"
            )
            return
        
        try:
            value = float(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Nilai harus angka!")
            return
        
        from_unit = context.args[1].lower()
        to_unit = context.args[2].lower()
        
        conversions = {
            ('km', 'mi'): lambda x: x * 0.621371,
            ('mi', 'km'): lambda x: x / 0.621371,
            ('kg', 'lbs'): lambda x: x * 2.20462,
            ('lbs', 'kg'): lambda x: x / 2.20462,
            ('c', 'f'): lambda x: (x * 9/5) + 32,
            ('f', 'c'): lambda x: (x - 32) * 5/9,
            ('m', 'ft'): lambda x: x * 3.28084,
            ('ft', 'm'): lambda x: x / 3.28084,
            ('cm', 'in'): lambda x: x / 2.54,
            ('in', 'cm'): lambda x: x * 2.54,
        }
        
        key = (from_unit, to_unit)
        if key in conversions:
            result = conversions[key](value)
            await update.message.reply_text(
                f"🔄 **Conversion:**\n{value} {from_unit.upper()} = {result:.4f} {to_unit.upper()}"
            )
        else:
            available = ", ".join([f"{a}->{b}" for (a, b) in conversions.keys()])
            await update.message.reply_text(f"❌ Konversi tidak didukung!\nSupported: {available}")
        
        log_action(self.bot_name, "convert", update.effective_user.id, f"{value}{from_unit} to {to_unit}")
    
    async def random_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate random number"""
        max_value = int(context.args[0]) if context.args else 100
        
        if max_value < 1:
            await update.message.reply_text("❌ Max value harus lebih dari 0")
            return
        
        result = random.randint(1, max_value)
        await update.message.reply_text(f"🎲 Random number (1-{max_value}): **{result}**", parse_mode='Markdown')
    
    async def coin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Flip coin"""
        result = random.choice(['Heads', 'Tails'])
        emoji = '🟡' if result == 'Heads' else '⚪'
        await update.message.reply_text(f"🪙 Coin flip: **{emoji} {result}**", parse_mode='Markdown')
        log_action(self.bot_name, "coin_flip", update.effective_user.id, result)
    
    async def dice_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Roll dice"""
        result = random.randint(1, 6)
        dice_emojis = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
        await update.message.reply_text(f"🎲 Dice roll: {dice_emojis[result-1]} ({result})")
        log_action(self.bot_name, "dice_roll", update.effective_user.id, str(result))
    
    async def decide_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help decide between options"""
        if not context.args:
            await update.message.reply_text(
                "Gunakan: /decide <pilihan1|pilihan2|pilihan3>\n"
                "Contoh: /decide Makan|Tidur|Belajar"
            )
            return
        
        options = " ".join(context.args).split('|')
        if len(options) < 2:
            await update.message.reply_text("❌ Minimal 2 pilihan diperlukan!")
            return
        
        choice = random.choice(options).strip()
        await update.message.reply_text(f"🤔 Saya memutuskan: **{choice}**", parse_mode='Markdown')
        log_action(self.bot_name, "decide", update.effective_user.id, f"chose: {choice}")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show usage statistics"""
        user_id = str(update.effective_user.id)
        
        total_notes = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM user_notes WHERE user_id = ?",
            (user_id,)
        )['count']
        
        total_quotes = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM favorite_quotes WHERE user_id = ?",
            (user_id,)
        )['count']
        
        active_reminders = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM reminders WHERE user_id = ? AND completed = 0",
            (user_id,)
        )['count']
        
        stats_text = f"""
📊 **MY STATISTICS**

📝 Notes: {total_notes}
💭 Saved Quotes: {total_quotes}
⏰ Active Reminders: {active_reminders}
"""
        await update.message.reply_text(stats_text)
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """About bot"""
        about_text = """
🤖 **UTILITY BOT**

Bot serbaguna dengan berbagai fitur utilitas untuk membantu aktivitas sehari-hari Anda.

✨ **Fitur Utama:**
• 🧮 Kalkulator ilmiah
• 💭 Quote generator & saver
• ⏰ Reminder & timer
• 📝 Catatan pribadi
• 🔄 Converter unit
• 🎲 Random tools

Dibuat untuk memudahkan hidup Anda!
"""
        await update.message.reply_text(about_text)
    
    def setup_handlers(self):
        """Setup semua command handlers"""
        # Basic commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("about", self.about_command))
        
        # Calculator
        self.app.add_handler(CommandHandler("calc", self.calc_command))
        
        # Quotes
        self.app.add_handler(CommandHandler("quote", self.quote_command))
        self.app.add_handler(CommandHandler("savequote", self.save_quote))
        self.app.add_handler(CommandHandler("myquotes", self.my_quotes))
        
        # Reminders
        self.app.add_handler(CommandHandler("remind", self.remind_command))
        self.app.add_handler(CommandHandler("reminders", self.list_reminders))
        
        # Timer
        self.app.add_handler(CommandHandler("timer", self.timer_command))
        
        # Notes
        self.app.add_handler(CommandHandler("note", self.note_command))
        self.app.add_handler(CommandHandler("notes", self.list_notes))
        self.app.add_handler(CommandHandler("getnote", self.get_note))
        self.app.add_handler(CommandHandler("delnote", self.del_note))
        
        # Converter
        self.app.add_handler(CommandHandler("convert", self.convert_command))
        
        # Random tools
        self.app.add_handler(CommandHandler("random", self.random_command))
        self.app.add_handler(CommandHandler("coin", self.coin_command))
        self.app.add_handler(CommandHandler("dice", self.dice_command))
        self.app.add_handler(CommandHandler("decide", self.decide_command))
        
        # Stats
        self.app.add_handler(CommandHandler("stats", self.stats_command))
    
    def run(self):
        """Jalankan bot"""
        print(f"🤖 Starting {self.bot_name}...")
        
        # Create application with job queue untuk reminders
        self.app = Application.builder().token(self.token).job_queue(JobQueue()).build()
        
        # Setup handlers
        self.setup_handlers()
        
        # Start bot
        print(f"✅ {self.bot_name} is running!")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Entry point untuk menjalankan bot"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Utility Bot')
    parser.add_argument('--token', type=str, required=True, help='Telegram Bot Token')
    parser.add_argument('--name', type=str, default='UtilityBot', help='Bot Name')
    
    args = parser.parse_args()
    
    bot = UtilityBot(token=args.token, bot_name=args.name)
    bot.run()


if __name__ == '__main__':
    main()
