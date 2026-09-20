"""
Group Manager Bot - Template Bot Telegram untuk Manajemen Grup
Fitur lengkap dengan database SQLite per bot
"""

import os
import sys
import re
import sqlite3
from datetime import datetime
from typing import Optional

# Setup logging
import logging
logging.basicConfig(
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

try:
    from telegram import Update, ChatPermissions
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    logger.info("Installing python-telegram-bot...")
    os.system("pip install python-telegram-bot==21.0")
    from telegram import Update, ChatPermissions
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


class GroupDatabase:
    """Database manager untuk Group Manager Bot (SQLite per bot)"""
    
    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        db_path = os.path.join(os.path.dirname(__file__), f'{bot_id}.db')
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.init_db()
        logger.info(f"[{bot_id}] Database initialized: {db_path}")
    
    def init_db(self):
        """Inisialisasi tabel-tabel"""
        # Tabel pengaturan grup
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_settings (
                chat_id TEXT PRIMARY KEY,
                welcome_message TEXT DEFAULT 'Selamat datang {name}! Selamat bergabung di {title}',
                goodbye_message TEXT DEFAULT '{name} telah meninggalkan grup',
                rules TEXT DEFAULT '',
                welcome_enabled INTEGER DEFAULT 1,
                goodbye_enabled INTEGER DEFAULT 1,
                antilink_enabled INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabel warnings
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                reason TEXT,
                warned_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabel custom commands
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_commands (
                chat_id TEXT NOT NULL,
                cmd_name TEXT NOT NULL,
                response TEXT NOT NULL,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, cmd_name)
            )
        ''')
        
        # Tabel banned users
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS banned_users (
                chat_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                reason TEXT,
                banned_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, user_id)
            )
        ''')
        
        self.conn.commit()
    
    def get_welcome(self, chat_id: str) -> tuple:
        self.cursor.execute('SELECT welcome_message, welcome_enabled FROM group_settings WHERE chat_id = ?', (chat_id,))
        result = self.cursor.fetchone()
        return (result[0], result[1]) if result else ('Selamat datang {name}!', 1)
    
    def set_welcome(self, chat_id: str, message: str):
        self.cursor.execute('''
            INSERT INTO group_settings (chat_id, welcome_message) 
            VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET welcome_message = excluded.welcome_message
        ''', (chat_id, message))
        self.conn.commit()
    
    def add_warning(self, chat_id: str, user_id: int, username: str, reason: str, warned_by: int):
        self.cursor.execute('''
            INSERT INTO warnings (chat_id, user_id, username, reason, warned_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (chat_id, user_id, username, reason, warned_by))
        self.conn.commit()
    
    def get_warnings_count(self, chat_id: str, user_id: int) -> int:
        self.cursor.execute('SELECT COUNT(*) FROM warnings WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
        return self.cursor.fetchone()[0]
    
    def clear_warnings(self, chat_id: str, user_id: int):
        self.cursor.execute('DELETE FROM warnings WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
        self.conn.commit()
    
    def add_custom_command(self, chat_id: str, cmd_name: str, response: str, created_by: int):
        self.cursor.execute('''
            INSERT OR REPLACE INTO custom_commands (chat_id, cmd_name, response, created_by)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, cmd_name.lower(), response, created_by))
        self.conn.commit()
    
    def get_custom_command(self, chat_id: str, cmd_name: str) -> Optional[str]:
        self.cursor.execute('SELECT response FROM custom_commands WHERE chat_id = ? AND cmd_name = ?', 
                          (chat_id, cmd_name.lower()))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def ban_user(self, chat_id: str, user_id: int, username: str, reason: str, banned_by: int):
        self.cursor.execute('''
            INSERT OR REPLACE INTO banned_users (chat_id, user_id, username, reason, banned_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (chat_id, user_id, username, reason, banned_by))
        self.conn.commit()
    
    def is_banned(self, chat_id: str, user_id: int) -> bool:
        self.cursor.execute('SELECT 1 FROM banned_users WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
        return self.cursor.fetchone() is not None
    
    def unban_user(self, chat_id: str, user_id: int):
        self.cursor.execute('DELETE FROM banned_users WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
        self.conn.commit()


class GroupManagerBot:
    """Main class untuk Group Manager Bot"""
    
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        self.bot_id = os.getenv('BOT_ID', 'group_manager')
        
        if not self.token:
            logger.error(f"[{self.bot_id}] BOT_TOKEN tidak ditemukan!")
            print("ERROR: BOT_TOKEN tidak ditemukan. Silakan set token bot Anda.")
            sys.exit(1)
        
        self.db = GroupDatabase(self.bot_id)
        self.app = Application.builder().token(self.token).build()
        self.setup_handlers()
        
        # Cache admin IDs per chat
        self.admin_cache = {}
    
    async def is_admin(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
        """Cek apakah user adalah admin"""
        cache_key = f"{chat_id}_{user_id}"
        if cache_key in self.admin_cache:
            return self.admin_cache[cache_key]
        
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            is_admin = member.status in ['administrator', 'creator']
            self.admin_cache[cache_key] = is_admin
            return is_admin
        except Exception:
            return False
    
    def setup_handlers(self):
        """Setup command dan message handlers"""
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("setwelcome", self.cmd_setwelcome))
        self.app.add_handler(CommandHandler("warn", self.cmd_warn))
        self.app.add_handler(CommandHandler("warnings", self.cmd_warnings))
        self.app.add_handler(CommandHandler("kick", self.cmd_kick))
        self.app.add_handler(CommandHandler("ban", self.cmd_ban))
        self.app.add_handler(CommandHandler("mute", self.cmd_mute))
        self.app.add_handler(CommandHandler("unmute", self.cmd_unmute))
        self.app.add_handler(CommandHandler("addcmd", self.cmd_addcmd))
        self.app.add_handler(CommandHandler("stats", self.cmd_stats))
        
        self.app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.on_new_member))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_custom_commands))
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👋 Halo! Saya Group Manager Bot.\n\n"
            "Gunakan /help untuk melihat daftar perintah."
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
📋 **GROUP MANAGER COMMANDS**

/warn <reason> - Warn user (reply pesan)
/warnings - Cek warning count
/kick - Kick user dari grup
/ban - Ban user dari grup
/mute <menit> - Mute user
/unmute - Unmute user
/setwelcome <pesan> - Set welcome message
/addcmd <nama> <response> - Custom command
/stats - Statistik grup
"""
        await update.message.reply_text(help_text)
    
    async def cmd_setwelcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not context.args:
            await update.message.reply_text("Gunakan: /setwelcome <pesan>")
            return
        
        message = ' '.join(context.args)
        chat_id = str(update.effective_chat.id)
        self.db.set_welcome(chat_id, message)
        await update.message.reply_text(f"✅ Welcome message diatur!")
    
    async def cmd_warn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.reply_to_message:
            await update.message.reply_text("Reply pesan user dengan /warn <alasan>")
            return
        
        if not await self.is_admin(context, update.effective_chat.id, update.effective_user.id):
            await update.message.reply_text("❌ Hanya admin!")
            return
        
        target = update.message.reply_to_message.from_user
        reason = ' '.join(context.args) if context.args else "No reason"
        
        chat_id = str(update.effective_chat.id)
        self.db.add_warning(chat_id, target.id, target.username or str(target.id), reason, update.effective_user.id)
        
        warn_count = self.db.get_warnings_count(chat_id, target.id)
        if warn_count >= 3:
            await target.ban(chat_id=update.effective_chat.id)
            self.db.clear_warnings(chat_id, target.id)
            await update.message.reply_text(f"⚠️ {target.mention_html()} kicked (3 warnings)!")
        else:
            await update.message.reply_text(f"⚠️ Warning #{warn_count} untuk {target.mention_html()}")
    
    async def cmd_warnings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.reply_to_message:
            return
        
        target = update.message.reply_to_message.from_user
        chat_id = str(update.effective_chat.id)
        count = self.db.get_warnings_count(chat_id, target.id)
        await update.message.reply_text(f"⚠️ {target.mention_html()} has {count} warning(s)")
    
    async def cmd_kick(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin(context, update.effective_chat.id, update.effective_user.id):
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply pesan user untuk kick")
            return
        
        target = update.message.reply_to_message.from_user
        await target.ban(chat_id=update.effective_chat.id)
        await update.effective_chat.unban_member(target.id)
        await update.message.reply_text(f"👢 {target.mention_html()} kicked!")
    
    async def cmd_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin(context, update.effective_chat.id, update.effective_user.id):
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply pesan user untuk ban")
            return
        
        target = update.message.reply_to_message.from_user
        chat_id = str(update.effective_chat.id)
        self.db.ban_user(chat_id, target.id, target.username or '', 'No reason', update.effective_user.id)
        
        await target.ban(chat_id=update.effective_chat.id)
        await update.message.reply_text(f"🚫 {target.mention_html()} banned!")
    
    async def cmd_mute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin(context, update.effective_chat.id, update.effective_user.id):
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply pesan user untuk mute")
            return
        
        target = update.message.reply_to_message.from_user
        minutes = int(context.args[0].replace('m', '')) if context.args else 10
        
        await update.effective_chat.restrict_member(
            target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=datetime.now().timestamp() + (minutes * 60)
        )
        await update.message.reply_text(f"🔇 Muted for {minutes} minutes")
    
    async def cmd_unmute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin(context, update.effective_chat.id, update.effective_user.id):
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply pesan user untuk unmute")
            return
        
        target = update.message.reply_to_message.from_user
        await update.effective_chat.restrict_member(
            target.id,
            permissions=ChatPermissions(can_send_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True)
        )
        await update.message.reply_text(f"🔊 Unmuted!")
    
    async def cmd_addcmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin(context, update.effective_chat.id, update.effective_user.id):
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Gunakan: /addcmd <nama> <response>")
            return
        
        cmd_name = context.args[0]
        response = ' '.join(context.args[1:])
        chat_id = str(update.effective_chat.id)
        
        self.db.add_custom_command(chat_id, cmd_name, response, update.effective_user.id)
        await update.message.reply_text(f"✅ Command /{cmd_name} added!")
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        members_count = await chat.get_member_count()
        await update.message.reply_text(f"📊 {chat.title}\nMembers: {members_count}")
    
    async def on_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        welcome_msg, enabled = self.db.get_welcome(chat_id)
        
        if not enabled:
            return
        
        for member in update.message.new_chat_members:
            msg = welcome_msg.format(name=member.first_name, title=update.effective_chat.title)
            await update.message.reply_text(msg)
    
    async def handle_custom_commands(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if not text or not text.startswith('/'):
            return
        
        cmd_name = text.split()[0][1:].lower()
        chat_id = str(update.effective_chat.id)
        
        response = self.db.get_custom_command(chat_id, cmd_name)
        if response:
            await update.message.reply_text(response)
    
    def run(self):
        logger.info(f"[{self.bot_id}] Starting...")
        print(f"[{self.bot_id}] Group Manager Bot running!")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    bot = GroupManagerBot()
    bot.run()
