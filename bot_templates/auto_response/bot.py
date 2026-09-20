"""
Bot Auto Response - Template Bot untuk Auto-Response Telegram
Fitur: Auto-reply berdasarkan keyword, AI-like responses, jadwal response
Setiap bot memiliki database SQLite sendiri
"""

import os
import sys
import re
from datetime import datetime
from typing import Optional

# Tambahkan shared_libs ke path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared_libs'))

from bot_utils import DatabaseManager, ModuleRegistry, sanitize_text, log_action

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    print("Installing python-telegram-bot...")
    os.system("pip install python-telegram-bot")
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


class AutoResponseDB(DatabaseManager):
    """Database manager khusus untuk Auto Response Bot"""
    
    def init_db(self):
        """Inisialisasi tabel-tabel untuk auto response"""
        # Tabel keyword responses
        self.execute('''
            CREATE TABLE IF NOT EXISTS keyword_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                keyword TEXT NOT NULL,
                response TEXT NOT NULL,
                exact_match INTEGER DEFAULT 0,
                case_sensitive INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                usage_count INTEGER DEFAULT 0,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chat_id, keyword)
            )
        ''')
        
        # Tabel scheduled responses
        self.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                message TEXT NOT NULL,
                schedule_type TEXT DEFAULT 'daily',
                schedule_time TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                last_sent TIMESTAMP,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabel smart patterns (regex)
        self.execute('''
            CREATE TABLE IF NOT EXISTS smart_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                pattern TEXT NOT NULL,
                response TEXT NOT NULL,
                flags TEXT DEFAULT '',
                active INTEGER DEFAULT 1,
                usage_count INTEGER DEFAULT 0,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabel conversation flows
        self.execute('''
            CREATE TABLE IF NOT EXISTS conversation_flows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                trigger_keyword TEXT NOT NULL,
                flow_data TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')


@ModuleRegistry.register('auto_response')
class AutoResponseModule:
    """Modul auto response berdasarkan keyword"""
    
    @staticmethod
    async def check_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE, db: AutoResponseDB):
        """Cek apakah pesan mengandung keyword yang terdaftar"""
        if not update.message or not update.message.text:
            return
        
        chat = update.effective_chat
        user = update.effective_user
        message_text = update.message.text
        
        # Cek global responses (chat_id = NULL)
        global_responses = db.fetch_all(
            "SELECT * FROM keyword_responses WHERE chat_id IS NULL AND active = 1"
        )
        
        # Cek chat-specific responses
        chat_responses = db.fetch_all(
            "SELECT * FROM keyword_responses WHERE chat_id = ? AND active = 1",
            (str(chat.id),)
        )
        
        all_responses = global_responses + chat_responses
        
        for resp in all_responses:
            keyword = resp['keyword']
            response = resp['response']
            exact_match = resp['exact_match']
            case_sensitive = resp['case_sensitive']
            
            search_text = message_text if case_sensitive else message_text.lower()
            search_keyword = keyword if case_sensitive else keyword.lower()
            
            matched = False
            if exact_match:
                matched = search_text == search_keyword
            else:
                matched = search_keyword in search_text
            
            if matched:
                await update.message.reply_text(sanitize_text(response))
                
                # Update usage count
                db.execute(
                    "UPDATE keyword_responses SET usage_count = usage_count + 1 WHERE id = ?",
                    (resp['id'],)
                )
                
                log_action("AutoResponse", "keyword_triggered", user.id, f"keyword: {keyword}")
                return


@ModuleRegistry.register('smart_pattern')
class SmartPatternModule:
    """Modul smart pattern matching dengan regex"""
    
    @staticmethod
    async def check_pattern(update: Update, context: ContextTypes.DEFAULT_TYPE, db: AutoResponseDB):
        """Cek apakah pesan match dengan pattern regex"""
        if not update.message or not update.message.text:
            return
        
        chat = update.effective_chat
        message_text = update.message.text
        
        # Cek global patterns
        global_patterns = db.fetch_all(
            "SELECT * FROM smart_patterns WHERE chat_id IS NULL AND active = 1"
        )
        
        # Cek chat-specific patterns
        chat_patterns = db.fetch_all(
            "SELECT * FROM smart_patterns WHERE chat_id = ? AND active = 1",
            (str(chat.id),)
        )
        
        all_patterns = global_patterns + chat_patterns
        
        for pattern_data in all_patterns:
            try:
                pattern = pattern_data['pattern']
                response = pattern_data['response']
                flags = pattern_data['flags']
                
                # Compile regex dengan flags
                flag_value = 0
                if 'i' in flags.lower():
                    flag_value |= re.IGNORECASE
                if 'm' in flags.lower():
                    flag_value |= re.MULTILINE
                if 's' in flags.lower():
                    flag_value |= re.DOTALL
                
                regex = re.compile(pattern, flag_value)
                
                if regex.search(message_text):
                    # Support capture groups dalam response
                    match = regex.search(message_text)
                    formatted_response = response
                    for i, group in enumerate(match.groups()):
                        formatted_response = formatted_response.replace(f'{{{i+1}}}', group or '')
                    
                    await update.message.reply_text(sanitize_text(formatted_response))
                    
                    # Update usage count
                    db.execute(
                        "UPDATE smart_patterns SET usage_count = usage_count + 1 WHERE id = ?",
                        (pattern_data['id'],)
                    )
                    
                    return
            except re.error as e:
                print(f"Invalid regex pattern: {pattern} - Error: {e}")


class AutoResponseBot:
    """Main class untuk Auto Response Bot"""
    
    def __init__(self, token: str, bot_name: str = "AutoResponse"):
        self.token = token
        self.bot_name = bot_name
        self.db_path = os.path.join(
            os.path.dirname(__file__), 
            'databases', 
            f'{bot_name}_{token[:8]}.db'
        )
        self.db = AutoResponseDB(self.db_path)
        self.app = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Command /start"""
        await update.message.reply_text(
            "👋 Halo! Saya adalah Bot Auto Response.\n\n"
            "Saya bisa menjawab pertanyaan secara otomatis berdasarkan keyword.\n"
            "Gunakan /help untuk melihat daftar perintah."
        )
        log_action(self.bot_name, "start", update.effective_user.id)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Command /help"""
        help_text = """
📋 **DAFTAR PERINTAH AUTO RESPONSE**

🔧 **Admin Commands:**
/addresponse <keyword> <response> - Tambah auto response
/delresponse <keyword> - Hapus auto response
/listresponse - List semua auto response
/toggleresponse <id> - Enable/disable response

🎯 **Smart Patterns (Regex):**
/addpattern <pattern> <response> - Tambah pattern regex
/delpattern <id> - Hapus pattern
/listpattern - List semua pattern

📊 **Stats:**
/stats - Lihat statistik response
/topkeywords - Lihat keyword paling sering dipicu

ℹ️ **Info:**
/about - Tentang bot ini
"""
        await update.message.reply_text(help_text)
    
    async def add_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Tambah auto response"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Untuk private chat, semua bisa tambah. Untuk grup, hanya admin
        if chat.type != 'private':
            admins = [admin.user.id for admin in await chat.get_administrators()]
            if user.id not in admins and user.id != chat.id:
                await update.message.reply_text("❌ Hanya admin yang bisa menambah response")
                return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Gunakan: /addresponse <keyword> <response>\n"
                "Contoh: /addresponse halo Halo juga! Apa kabar?"
            )
            return
        
        keyword = context.args[0]
        response = " ".join(context.args[1:])
        
        chat_id = str(chat.id) if chat.type != 'private' else None
        
        self.db.execute(
            """INSERT OR REPLACE INTO keyword_responses 
               (chat_id, keyword, response, created_by) VALUES (?, ?, ?, ?)""",
            (chat_id, keyword, response, str(user.id))
        )
        
        await update.message.reply_text(f"✅ Auto response untuk '{keyword}' berhasil ditambahkan")
        log_action(self.bot_name, "response_added", user.id, f"keyword: {keyword}")
    
    async def del_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hapus auto response"""
        chat = update.effective_chat
        user = update.effective_user
        
        if chat.type != 'private':
            admins = [admin.user.id for admin in await chat.get_administrators()]
            if user.id not in admins:
                await update.message.reply_text("❌ Hanya admin yang bisa menghapus response")
                return
        
        if not context.args:
            await update.message.reply_text("Gunakan: /delresponse <keyword>")
            return
        
        keyword = context.args[0]
        chat_id = str(chat.id) if chat.type != 'private' else None
        
        if chat_id:
            result = self.db.execute(
                "DELETE FROM keyword_responses WHERE chat_id = ? AND keyword = ?",
                (chat_id, keyword)
            )
        else:
            result = self.db.execute(
                "DELETE FROM keyword_responses WHERE keyword = ? AND chat_id IS NULL",
                (keyword,)
            )
        
        if result.rowcount > 0:
            await update.message.reply_text(f"✅ Auto response '{keyword}' berhasil dihapus")
        else:
            await update.message.reply_text(f"❌ Keyword '{keyword}' tidak ditemukan")
        
        log_action(self.bot_name, "response_deleted", user.id, f"keyword: {keyword}")
    
    async def list_responses(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List semua auto response"""
        chat = update.effective_chat
        chat_id = str(chat.id) if chat.type != 'private' else None
        
        if chat_id:
            responses = self.db.fetch_all(
                "SELECT * FROM keyword_responses WHERE chat_id = ? ORDER BY keyword",
                (chat_id,)
            )
        else:
            responses = self.db.fetch_all(
                "SELECT * FROM keyword_responses WHERE chat_id IS NULL ORDER BY keyword"
            )
        
        if not responses:
            await update.message.reply_text("📝 Belum ada auto response")
            return
        
        response_list = []
        for i, resp in enumerate(responses[:20], 1):  # Limit 20
            status = "🟢" if resp['active'] else "🔴"
            match_type = "exact" if resp['exact_match'] else "contains"
            response_list.append(
                f"{i}. {status} {resp['keyword']} ({match_type})\n"
                f"   → {resp['response'][:50]}..."
            )
        
        if len(responses) > 20:
            response_list.append(f"... dan {len(responses) - 20} lainnya")
        
        await update.message.reply_text("📋 **Auto Responses:**\n\n" + "\n".join(response_list))
    
    async def toggle_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enable/disable auto response"""
        chat = update.effective_chat
        user = update.effective_user
        
        if chat.type != 'private':
            admins = [admin.user.id for admin in await chat.get_administrators()]
            if user.id not in admins:
                await update.message.reply_text("❌ Hanya admin yang bisa toggle response")
                return
        
        if not context.args:
            await update.message.reply_text("Gunakan: /toggleresponse <id>")
            return
        
        try:
            resp_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("ID harus berupa angka")
            return
        
        response = self.db.fetch_one("SELECT * FROM keyword_responses WHERE id = ?", (resp_id,))
        
        if not response:
            await update.message.reply_text("❌ Response tidak ditemukan")
            return
        
        new_status = 0 if response['active'] else 1
        self.db.execute(
            "UPDATE keyword_responses SET active = ? WHERE id = ?",
            (new_status, resp_id)
        )
        
        status = "diaktifkan" if new_status else "dinonaktifkan"
        await update.message.reply_text(f"✅ Response '{response['keyword']}' berhasil {status}")
        log_action(self.bot_name, "response_toggled", user.id, f"id: {resp_id}")
    
    async def add_pattern(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Tambah smart pattern (regex)"""
        chat = update.effective_chat
        user = update.effective_user
        
        if chat.type != 'private':
            admins = [admin.user.id for admin in await chat.get_administrators()]
            if user.id not in admins:
                await update.message.reply_text("❌ Hanya admin yang bisa menambah pattern")
                return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Gunakan: /addpattern <pattern> <response>\n"
                "Contoh: /addpattern harga.*rp(\\d+) Harga adalah Rp{1}\n"
                "Flags bisa ditambahkan: /addpattern pattern response --flags=im"
            )
            return
        
        args = " ".join(context.args)
        flags = ""
        
        # Parse flags
        if '--flags=' in args:
            parts = args.split('--flags=')
            args = parts[0].strip()
            flags = parts[1].split()[0]
        
        # Split pattern dan response (asumsi dipisahkan oleh newline atau |)
        if '\n' in args:
            pattern, response = args.split('\n', 1)
        elif '|' in args:
            pattern, response = args.split('|', 1)
        else:
            pattern = context.args[0]
            response = " ".join(context.args[1:])
        
        chat_id = str(chat.id) if chat.type != 'private' else None
        
        self.db.execute(
            """INSERT INTO smart_patterns 
               (chat_id, pattern, response, flags, created_by) VALUES (?, ?, ?, ?, ?)""",
            (chat_id, pattern, response, flags, str(user.id))
        )
        
        await update.message.reply_text(f"✅ Pattern regex berhasil ditambahkan")
        log_action(self.bot_name, "pattern_added", user.id, f"pattern: {pattern[:30]}")
    
    async def list_patterns(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List semua smart patterns"""
        chat = update.effective_chat
        chat_id = str(chat.id) if chat.type != 'private' else None
        
        if chat_id:
            patterns = self.db.fetch_all(
                "SELECT * FROM smart_patterns WHERE chat_id = ? ORDER BY id",
                (chat_id,)
            )
        else:
            patterns = self.db.fetch_all(
                "SELECT * FROM smart_patterns WHERE chat_id IS NULL ORDER BY id"
            )
        
        if not patterns:
            await update.message.reply_text("📝 Belum ada smart pattern")
            return
        
        pattern_list = []
        for i, p in enumerate(patterns[:15], 1):
            status = "🟢" if p['active'] else "🔴"
            pattern_list.append(
                f"{i}. {status} `{p['pattern']}`\n"
                f"   → {p['response'][:40]}...\n"
                f"   Flags: {p['flags'] or '-'} | Usage: {p['usage_count']}"
            )
        
        await update.message.reply_text("📋 **Smart Patterns:**\n\n" + "\n".join(pattern_list))
    
    async def del_pattern(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hapus smart pattern"""
        chat = update.effective_chat
        user = update.effective_user
        
        if chat.type != 'private':
            admins = [admin.user.id for admin in await chat.get_administrators()]
            if user.id not in admins:
                await update.message.reply_text("❌ Hanya admin yang bisa menghapus pattern")
                return
        
        if not context.args:
            await update.message.reply_text("Gunakan: /delpattern <id>")
            return
        
        try:
            pattern_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("ID harus berupa angka")
            return
        
        result = self.db.execute(
            "DELETE FROM smart_patterns WHERE id = ?",
            (pattern_id,)
        )
        
        if result.rowcount > 0:
            await update.message.reply_text(f"✅ Pattern ID {pattern_id} berhasil dihapus")
        else:
            await update.message.reply_text(f"❌ Pattern ID {pattern_id} tidak ditemukan")
        
        log_action(self.bot_name, "pattern_deleted", user.id, f"id: {pattern_id}")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show statistik"""
        chat = update.effective_chat
        chat_id = str(chat.id) if chat.type != 'private' else None
        
        if chat_id:
            total_responses = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM keyword_responses WHERE chat_id = ?",
                (chat_id,)
            )['count']
            
            total_patterns = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM smart_patterns WHERE chat_id = ?",
                (chat_id,)
            )['count']
            
            total_usage = self.db.fetch_one(
                "SELECT SUM(usage_count) as count FROM keyword_responses WHERE chat_id = ?",
                (chat_id,)
            )['count'] or 0
        else:
            total_responses = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM keyword_responses WHERE chat_id IS NULL"
            )['count']
            
            total_patterns = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM smart_patterns WHERE chat_id IS NULL"
            )['count']
            
            total_usage = self.db.fetch_one(
                "SELECT SUM(usage_count) as count FROM keyword_responses WHERE chat_id IS NULL"
            )['count'] or 0
        
        stats_text = f"""
📊 **STATISTIK AUTO RESPONSE**

📝 Total Responses: {total_responses}
🎯 Total Patterns: {total_patterns}
📈 Total Triggered: {total_usage}
"""
        await update.message.reply_text(stats_text)
    
    async def top_keywords(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show top keywords"""
        chat = update.effective_chat
        chat_id = str(chat.id) if chat.type != 'private' else None
        
        if chat_id:
            keywords = self.db.fetch_all(
                """SELECT keyword, usage_count FROM keyword_responses 
                   WHERE chat_id = ? AND usage_count > 0 
                   ORDER BY usage_count DESC LIMIT 10""",
                (chat_id,)
            )
        else:
            keywords = self.db.fetch_all(
                """SELECT keyword, usage_count FROM keyword_responses 
                   WHERE chat_id IS NULL AND usage_count > 0 
                   ORDER BY usage_count DESC LIMIT 10"""
            )
        
        if not keywords:
            await update.message.reply_text("📝 Belum ada keyword yang dipicu")
            return
        
        top_list = "\n".join([
            f"{i+1}. {k['keyword']} - {k['usage_count']}x"
            for i, k in enumerate(keywords)
        ])
        
        await update.message.reply_text(f"🔥 **Top Keywords:**\n\n{top_list}")
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """About bot"""
        about_text = """
🤖 **AUTO RESPONSE BOT**

Bot ini dapat menjawab pertanyaan secara otomatis berdasarkan keyword atau pattern regex yang Anda tentukan.

✨ **Fitur:**
• Auto-response berdasarkan keyword
• Smart pattern matching dengan regex
• Support capture groups
• Statistik penggunaan
• Global dan chat-specific responses

Dibuat untuk memudahkan manajemen jawaban otomatis di Telegram.
"""
        await update.message.reply_text(about_text)
    
    def setup_handlers(self):
        """Setup semua command handlers"""
        # Basic commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("about", self.about_command))
        
        # Response management
        self.app.add_handler(CommandHandler("addresponse", self.add_response))
        self.app.add_handler(CommandHandler("delresponse", self.del_response))
        self.app.add_handler(CommandHandler("listresponse", self.list_responses))
        self.app.add_handler(CommandHandler("toggleresponse", self.toggle_response))
        
        # Pattern management
        self.app.add_handler(CommandHandler("addpattern", self.add_pattern))
        self.app.add_handler(CommandHandler("delpattern", self.del_pattern))
        self.app.add_handler(CommandHandler("listpattern", self.list_patterns))
        
        # Stats
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("topkeywords", self.top_keywords))
        
        # Auto response handlers (harus terakhir)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, AutoResponseModule.check_keyword))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, SmartPatternModule.check_pattern))
    
    def run(self):
        """Jalankan bot"""
        print(f"🤖 Starting {self.bot_name}...")
        
        # Create application
        self.app = Application.builder().token(self.token).build()
        
        # Setup handlers
        self.setup_handlers()
        
        # Start bot
        print(f"✅ {self.bot_name} is running!")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Entry point untuk menjalankan bot"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto Response Bot')
    parser.add_argument('--token', type=str, required=True, help='Telegram Bot Token')
    parser.add_argument('--name', type=str, default='AutoResponse', help='Bot Name')
    
    args = parser.parse_args()
    
    bot = AutoResponseBot(token=args.token, bot_name=args.name)
    bot.run()


if __name__ == '__main__':
    main()
