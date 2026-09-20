"""
Bot Manager Group - Template Bot untuk Manajemen Grup Telegram
Fitur: Welcome message, anti-spam, kick/ban, warn system, rules, dan lain-lain
Setiap bot memiliki database SQLite sendiri
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# Tambahkan shared_libs ke path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared_libs'))

from bot_utils import DatabaseManager, ModuleRegistry, sanitize_text, is_admin, log_action

try:
    from telegram import Update, ChatPermissions
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    print("Installing python-telegram-bot...")
    os.system("pip install python-telegram-bot")
    from telegram import Update, ChatPermissions
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


class GroupManagerDB(DatabaseManager):
    """Database manager khusus untuk Group Manager Bot"""
    
    def init_db(self):
        """Inisialisasi tabel-tabel untuk group manager"""
        # Tabel pengaturan grup
        self.execute('''
            CREATE TABLE IF NOT EXISTS group_settings (
                chat_id TEXT PRIMARY KEY,
                welcome_message TEXT DEFAULT 'Selamat datang {name}! Selamat bergabung di {title}',
                goodbye_message TEXT DEFAULT '{name} telah meninggalkan grup',
                rules TEXT DEFAULT '',
                welcome_enabled INTEGER DEFAULT 1,
                goodbye_enabled INTEGER DEFAULT 1,
                antiflood_enabled INTEGER DEFAULT 0,
                antiflood_limit INTEGER DEFAULT 5,
                antilink_enabled INTEGER DEFAULT 0,
                antispam_enabled INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabel warnings
        self.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                warned_by TEXT NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabel banned users
        self.execute('''
            CREATE TABLE IF NOT EXISTS banned_users (
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                banned_by TEXT NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, user_id)
            )
        ''')
        
        # Tabel flood control
        self.execute('''
            CREATE TABLE IF NOT EXISTS user_messages (
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                message_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, user_id, message_time)
            )
        ''')
        
        # Tabel custom commands
        self.execute('''
            CREATE TABLE IF NOT EXISTS custom_commands (
                chat_id TEXT NOT NULL,
                command TEXT NOT NULL,
                response TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, command)
            )
        ''')


@ModuleRegistry.register('welcome')
class WelcomeModule:
    """Modul welcome message"""
    
    @staticmethod
    async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE, db: GroupManagerDB):
        """Handle anggota baru yang bergabung"""
        chat = update.effective_chat
        settings = db.fetch_one(
            "SELECT welcome_message, welcome_enabled FROM group_settings WHERE chat_id = ?",
            (str(chat.id),)
        )
        
        if not settings or not settings['welcome_enabled']:
            return
        
        for user in update.message.new_chat_members:
            name = user.first_name
            if user.last_name:
                name += f" {user.last_name}"
            
            welcome_msg = settings['welcome_message'].format(
                name=name,
                title=chat.title,
                username=f"@{user.username}" if user.username else name
            )
            
            await context.bot.send_message(
                chat_id=chat.id,
                text=sanitize_text(welcome_msg)
            )
            
            log_action("GroupManager", "welcome_sent", user.id, f"chat {chat.id}")


@ModuleRegistry.register('goodbye')
class GoodbyeModule:
    """Modul goodbye message"""
    
    @staticmethod
    async def handle_left_member(update: Update, context: ContextTypes.DEFAULT_TYPE, db: GroupManagerDB):
        """Handle anggota yang keluar"""
        chat = update.effective_chat
        settings = db.fetch_one(
            "SELECT goodbye_message, goodbye_enabled FROM group_settings WHERE chat_id = ?",
            (str(chat.id),)
        )
        
        if not settings or not settings['goodbye_enabled']:
            return
        
        user = update.message.left_chat_member
        name = user.first_name
        if user.last_name:
            name += f" {user.last_name}"
        
        goodbye_msg = settings['goodbye_message'].format(
            name=name,
            title=chat.title,
            username=f"@{user.username}" if user.username else name
        )
        
        await context.bot.send_message(
            chat_id=chat.id,
            text=sanitize_text(goodbye_msg)
        )


@ModuleRegistry.register('antilink')
class AntiLinkModule:
    """Modul anti link"""
    
    LINK_PATTERNS = ['http://', 'https://', 't.me/', 'telegram.me/']
    
    @staticmethod
    async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE, db: GroupManagerDB):
        """Cek apakah pesan mengandung link"""
        if not update.message or not update.message.text:
            return
        
        chat = update.effective_chat
        settings = db.fetch_one(
            "SELECT antilink_enabled FROM group_settings WHERE chat_id = ?",
            (str(chat.id),)
        )
        
        if not settings or not settings['antilink_enabled']:
            return
        
        message_text = update.message.text.lower()
        has_link = any(pattern in message_text for pattern in AntiLinkModule.LINK_PATTERNS)
        
        if has_link:
            # Cek apakah admin
            user = update.effective_user
            admins = [admin.user.id for admin in await chat.get_administrators()]
            
            if not is_admin(user.id, admins):
                await update.message.delete()
                warning_msg = await update.message.reply_text(
                    f"⚠️ @{user.username} dilarang mengirim link di grup ini!"
                )
                await asyncio.sleep(5)
                await warning_msg.delete()
                
                log_action("GroupManager", "link_deleted", user.id, f"chat {chat.id}")


@ModuleRegistry.register('warn')
class WarnModule:
    """Modul warning system"""
    
    @staticmethod
    async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE, db: GroupManagerDB, reason: str = ""):
        """Tambah warning ke user"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Cek apakah perintah dari admin
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            return
        
        # Parse target user dan alasan
        args = context.args
        if not args:
            await update.message.reply_text("Gunakan: /warn @username [alasan]")
            return
        
        target_user = None
        reason = " ".join(args[1:]) if len(args) > 1 else "Tidak ada alasan"
        
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
        elif args[0].startswith('@'):
            # Coba dapatkan user dari username (terbatas)
            await update.message.reply_text("Mohon reply pesan user atau gunakan user ID")
            return
        
        if not target_user:
            return
        
        # Tambahkan warning
        db.execute(
            "INSERT INTO warnings (chat_id, user_id, warned_by, reason) VALUES (?, ?, ?, ?)",
            (str(chat.id), str(target_user.id), str(user.id), reason)
        )
        
        # Hitung total warnings
        warnings = db.fetch_all(
            "SELECT * FROM warnings WHERE chat_id = ? AND user_id = ?",
            (str(chat.id), str(target_user.id))
        )
        
        warn_count = len(warnings)
        await update.message.reply_text(
            f"⚠️ User {target_user.first_name} mendapat warning! ({warn_count}/3)\n"
            f"Alasan: {reason}"
        )
        
        # Auto kick jika 3 warnings
        if warn_count >= 3:
            try:
                await chat.ban_member(target_user.id)
                await update.message.reply_text(
                    f"🔨 User {target_user.first_name} di-kick karena mencapai 3 warnings!"
                )
                # Hapus warnings setelah kick
                db.execute(
                    "DELETE FROM warnings WHERE chat_id = ? AND user_id = ?",
                    (str(chat.id), str(target_user.id))
                )
            except Exception as e:
                await update.message.reply_text(f"Gagal kick user: {str(e)}")
        
        log_action("GroupManager", "warn_added", target_user.id, f"reason: {reason}")
    
    @staticmethod
    async def list_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE, db: GroupManagerDB):
        """List semua warnings user"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            return
        
        target_user = None
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
        
        if not target_user:
            await update.message.reply_text("Reply pesan user untuk melihat warnings")
            return
        
        warnings = db.fetch_all(
            "SELECT * FROM warnings WHERE chat_id = ? AND user_id = ? ORDER BY created_at DESC",
            (str(chat.id), str(target_user.id))
        )
        
        if not warnings:
            await update.message.reply_text(f"✅ {target_user.first_name} tidak memiliki warnings")
            return
        
        warn_list = "\n".join([
            f"{i+1}. {w['reason']} - {w['created_at']}" 
            for i, w in enumerate(warnings)
        ])
        
        await update.message.reply_text(
            f"⚠️ Warnings untuk {target_user.first_name}:\n\n{warn_list}"
        )
    
    @staticmethod
    async def reset_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE, db: GroupManagerDB):
        """Reset warnings user"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            return
        
        target_user = None
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
        
        if not target_user:
            await update.message.reply_text("Reply pesan user untuk reset warnings")
            return
        
        db.execute(
            "DELETE FROM warnings WHERE chat_id = ? AND user_id = ?",
            (str(chat.id), str(target_user.id))
        )
        
        await update.message.reply_text(f"✅ Warnings {target_user.first_name} telah direset")
        log_action("GroupManager", "warnings_reset", target_user.id)


class GroupManagerBot:
    """Main class untuk Group Manager Bot"""
    
    def __init__(self, token: str, bot_name: str = "GroupManager"):
        self.token = token
        self.bot_name = bot_name
        self.db_path = os.path.join(
            os.path.dirname(__file__), 
            'databases', 
            f'{bot_name}_{token[:8]}.db'
        )
        self.db = GroupManagerDB(self.db_path)
        self.app = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Command /start"""
        await update.message.reply_text(
            "👋 Halo! Saya adalah Bot Manager Grup.\n\n"
            "Gunakan /help untuk melihat daftar perintah."
        )
        log_action(self.bot_name, "start", update.effective_user.id)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Command /help"""
        help_text = """
📋 **DAFTAR PERINTAH GROUP MANAGER**

🔧 **Admin Commands:**
/warn - Beri warning ke user
/warnlist - Lihat warnings user
/resetwarn - Reset warnings user
/ban - Ban user dari grup
/unban - Unban user
/kick - Kick user dari grup
/mute - Mute user
/unmute - Unmute user

⚙️ **Settings:**
/setwelcome - Set welcome message
/setgoodbye - Set goodbye message
/setrules - Set rules grup
/togglewelcome - Enable/disable welcome
/togglegoodbye - Enable/disable goodbye
/toggleantilink - Enable/disable anti link

📝 **Custom Commands:**
/addcmd - Tambah custom command
/delcmd - Hapus custom command
/listcmd - List semua custom command

ℹ️ **Info:**
/rules - Lihat rules grup
/stats - Lihat statistik grup
"""
        await update.message.reply_text(help_text)
    
    async def set_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set welcome message"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            await update.message.reply_text("❌ Hanya admin yang bisa mengubah pengaturan")
            return
        
        if not context.args:
            await update.message.reply_text(
                "Gunakan: /setwelcome <pesan>\n"
                "Variabel: {name}, {title}, {username}"
            )
            return
        
        message = " ".join(context.args)
        self.db.execute(
            "INSERT OR REPLACE INTO group_settings (chat_id, welcome_message) VALUES (?, ?)",
            (str(chat.id), message)
        )
        
        await update.message.reply_text("✅ Welcome message berhasil diubah")
        log_action(self.bot_name, "welcome_set", user.id, f"chat {chat.id}")
    
    async def set_goodbye(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set goodbye message"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            await update.message.reply_text("❌ Hanya admin yang bisa mengubah pengaturan")
            return
        
        if not context.args:
            await update.message.reply_text(
                "Gunakan: /setgoodbye <pesan>\n"
                "Variabel: {name}, {title}, {username}"
            )
            return
        
        message = " ".join(context.args)
        self.db.execute(
            "INSERT OR REPLACE INTO group_settings (chat_id, goodbye_message) VALUES (?, ?)",
            (str(chat.id), message)
        )
        
        await update.message.reply_text("✅ Goodbye message berhasil diubah")
        log_action(self.bot_name, "goodbye_set", user.id, f"chat {chat.id}")
    
    async def set_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set group rules"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            await update.message.reply_text("❌ Hanya admin yang bisa mengubah pengaturan")
            return
        
        if not context.args:
            await update.message.reply_text("Gunakan: /setrules <rules>")
            return
        
        rules = " ".join(context.args)
        self.db.execute(
            "INSERT OR REPLACE INTO group_settings (chat_id, rules) VALUES (?, ?)",
            (str(chat.id), rules)
        )
        
        await update.message.reply_text("✅ Rules berhasil diubah")
        log_action(self.bot_name, "rules_set", user.id, f"chat {chat.id}")
    
    async def show_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show group rules"""
        chat = update.effective_chat
        settings = self.db.fetch_one(
            "SELECT rules FROM group_settings WHERE chat_id = ?",
            (str(chat.id),)
        )
        
        if not settings or not settings['rules']:
            await update.message.reply_text("📜 Belum ada rules yang ditetapkan")
            return
        
        await update.message.reply_text(f"📜 **RULES GRUP**\n\n{settings['rules']}")
    
    async def toggle_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle welcome message"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            await update.message.reply_text("❌ Hanya admin yang bisa mengubah pengaturan")
            return
        
        settings = self.db.fetch_one(
            "SELECT welcome_enabled FROM group_settings WHERE chat_id = ?",
            (str(chat.id),)
        )
        
        current = settings['welcome_enabled'] if settings else 1
        new_value = 0 if current else 1
        
        self.db.execute(
            "INSERT OR REPLACE INTO group_settings (chat_id, welcome_enabled) VALUES (?, ?)",
            (str(chat.id), new_value)
        )
        
        status = "diaktifkan" if new_value else "dinonaktifkan"
        await update.message.reply_text(f"✅ Welcome message {status}")
        log_action(self.bot_name, "welcome_toggled", user.id, f"status: {status}")
    
    async def toggle_goodbye(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle goodbye message"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            await update.message.reply_text("❌ Hanya admin yang bisa mengubah pengaturan")
            return
        
        settings = self.db.fetch_one(
            "SELECT goodbye_enabled FROM group_settings WHERE chat_id = ?",
            (str(chat.id),)
        )
        
        current = settings['goodbye_enabled'] if settings else 1
        new_value = 0 if current else 1
        
        self.db.execute(
            "INSERT OR REPLACE INTO group_settings (chat_id, goodbye_enabled) VALUES (?, ?)",
            (str(chat.id), new_value)
        )
        
        status = "diaktifkan" if new_value else "dinonaktifkan"
        await update.message.reply_text(f"✅ Goodbye message {status}")
        log_action(self.bot_name, "goodbye_toggled", user.id, f"status: {status}")
    
    async def toggle_antilink(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle anti link"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            await update.message.reply_text("❌ Hanya admin yang bisa mengubah pengaturan")
            return
        
        settings = self.db.fetch_one(
            "SELECT antilink_enabled FROM group_settings WHERE chat_id = ?",
            (str(chat.id),)
        )
        
        current = settings['antilink_enabled'] if settings else 0
        new_value = 0 if current else 1
        
        self.db.execute(
            "INSERT OR REPLACE INTO group_settings (chat_id, antilink_enabled) VALUES (?, ?)",
            (str(chat.id), new_value)
        )
        
        status = "diaktifkan" if new_value else "dinonaktifkan"
        await update.message.reply_text(f"✅ Anti-link {status}")
        log_action(self.bot_name, "antilink_toggled", user.id, f"status: {status}")
    
    async def ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban user dari grup"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            await update.message.reply_text("❌ Hanya admin yang bisa melakukan ini")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply pesan user yang ingin di-ban")
            return
        
        target_user = update.message.reply_to_message.from_user
        reason = " ".join(context.args) if context.args else "Tidak ada alasan"
        
        try:
            await chat.ban_member(target_user.id)
            await update.message.reply_text(
                f"🔨 {target_user.first_name} telah di-ban!\nAlasan: {reason}"
            )
            
            # Simpan ke database
            self.db.execute(
                "INSERT OR REPLACE INTO banned_users (chat_id, user_id, banned_by, reason) VALUES (?, ?, ?, ?)",
                (str(chat.id), str(target_user.id), str(user.id), reason)
            )
            
            log_action(self.bot_name, "ban", target_user.id, f"reason: {reason}")
        except Exception as e:
            await update.message.reply_text(f"Gagal ban user: {str(e)}")
    
    async def kick_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Kick user dari grup"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            await update.message.reply_text("❌ Hanya admin yang bisa melakukan ini")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply pesan user yang ingin di-kick")
            return
        
        target_user = update.message.reply_to_message.from_user
        reason = " ".join(context.args) if context.args else "Tidak ada alasan"
        
        try:
            await chat.ban_member(target_user.id, until_date=datetime.now() + timedelta(seconds=30))
            await update.message.reply_text(
                f"👢 {target_user.first_name} telah di-kick!\nAlasan: {reason}"
            )
            log_action(self.bot_name, "kick", target_user.id, f"reason: {reason}")
        except Exception as e:
            await update.message.reply_text(f"Gagal kick user: {str(e)}")
    
    async def mute_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mute user (tidak bisa kirim pesan)"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            await update.message.reply_text("❌ Hanya admin yang bisa melakukan ini")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply pesan user yang ingin di-mute")
            return
        
        target_user = update.message.reply_to_message.from_user
        
        try:
            await chat.restrict_member(
                target_user.id,
                ChatPermissions(can_send_messages=False),
            )
            await update.message.reply_text(f"🔇 {target_user.first_name} telah di-mute!")
            log_action(self.bot_name, "mute", target_user.id)
        except Exception as e:
            await update.message.reply_text(f"Gagal mute user: {str(e)}")
    
    async def unmute_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unmute user"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            await update.message.reply_text("❌ Hanya admin yang bisa melakukan ini")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply pesan user yang ingin di-unmute")
            return
        
        target_user = update.message.reply_to_message.from_user
        
        try:
            await chat.restrict_member(
                target_user.id,
                ChatPermissions(
                    can_send_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_change_info=False,
                    can_invite_users=True,
                    can_pin_messages=False,
                ),
            )
            await update.message.reply_text(f"🔊 {target_user.first_name} telah di-unmute!")
            log_action(self.bot_name, "unmute", target_user.id)
        except Exception as e:
            await update.message.reply_text(f"Gagal unmute user: {str(e)}")
    
    async def add_custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Tambah custom command"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            await update.message.reply_text("❌ Hanya admin yang bisa menambah command")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Gunakan: /addcmd <command> <response>\nContoh: /addcmd halo Halo juga!"
            )
            return
        
        cmd = context.args[0].lower()
        if cmd.startswith('/'):
            cmd = cmd[1:]
        
        response = " ".join(context.args[1:])
        
        self.db.execute(
            "INSERT OR REPLACE INTO custom_commands (chat_id, command, response, created_by) VALUES (?, ?, ?, ?)",
            (str(chat.id), cmd, response, str(user.id))
        )
        
        await update.message.reply_text(f"✅ Command /{cmd} berhasil ditambahkan")
        log_action(self.bot_name, "cmd_added", user.id, f"command: {cmd}")
    
    async def del_custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hapus custom command"""
        chat = update.effective_chat
        user = update.effective_user
        
        admins = [admin.user.id for admin in await chat.get_administrators()]
        if not is_admin(user.id, admins):
            await update.message.reply_text("❌ Hanya admin yang bisa menghapus command")
            return
        
        if not context.args:
            await update.message.reply_text("Gunakan: /delcmd <command>")
            return
        
        cmd = context.args[0].lower()
        if cmd.startswith('/'):
            cmd = cmd[1:]
        
        self.db.execute(
            "DELETE FROM custom_commands WHERE chat_id = ? AND command = ?",
            (str(chat.id), cmd)
        )
        
        await update.message.reply_text(f"✅ Command /{cmd} berhasil dihapus")
        log_action(self.bot_name, "cmd_deleted", user.id, f"command: {cmd}")
    
    async def list_custom_commands(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List semua custom command"""
        chat = update.effective_chat
        
        commands = self.db.fetch_all(
            "SELECT command FROM custom_commands WHERE chat_id = ?",
            (str(chat.id),)
        )
        
        if not commands:
            await update.message.reply_text("📝 Belum ada custom command")
            return
        
        cmd_list = "\n".join([f"/{c['command']}" for c in commands])
        await update.message.reply_text(f"📋 **Custom Commands:**\n\n{cmd_list}")
    
    async def handle_custom_commands(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle custom commands"""
        if not update.message or not update.message.text:
            return
        
        chat = update.effective_chat
        text = update.message.text
        
        if text.startswith('/'):
            cmd = text.split()[0][1:].lower()
            
            custom_cmd = self.db.fetch_one(
                "SELECT response FROM custom_commands WHERE chat_id = ? AND command = ?",
                (str(chat.id), cmd)
            )
            
            if custom_cmd:
                await update.message.reply_text(custom_cmd['response'])
                return
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show grup statistics"""
        chat = update.effective_chat
        
        try:
            member_count = await chat.get_member_count()
            admins = await chat.get_administrators()
            
            # Hitung warnings
            total_warnings = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM warnings WHERE chat_id = ?",
                (str(chat.id),)
            )['count']
            
            # Hitung banned users
            banned_count = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM banned_users WHERE chat_id = ?",
                (str(chat.id),)
            )['count']
            
            stats_text = f"""
📊 **STATISTIK GRUP**

👥 Anggota: {member_count}
👮 Admin: {len(admins)}
⚠️ Total Warnings: {total_warnings}
🚫 Users Banned: {banned_count}
📛 Nama: {chat.title}
🆔 ID: {chat.id}
"""
            await update.message.reply_text(stats_text)
        except Exception as e:
            await update.message.reply_text(f"Gagal mengambil statistik: {str(e)}")
    
    def setup_handlers(self):
        """Setup semua command handlers"""
        # Basic commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Settings commands
        self.app.add_handler(CommandHandler("setwelcome", self.set_welcome))
        self.app.add_handler(CommandHandler("setgoodbye", self.set_goodbye))
        self.app.add_handler(CommandHandler("setrules", self.set_rules))
        self.app.add_handler(CommandHandler("rules", self.show_rules))
        self.app.add_handler(CommandHandler("togglewelcome", self.toggle_welcome))
        self.app.add_handler(CommandHandler("togglegoodbye", self.toggle_goodbye))
        self.app.add_handler(CommandHandler("toggleantilink", self.toggle_antilink))
        
        # Moderation commands
        self.app.add_handler(CommandHandler("ban", self.ban_user))
        self.app.add_handler(CommandHandler("kick", self.kick_user))
        self.app.add_handler(CommandHandler("mute", self.mute_user))
        self.app.add_handler(CommandHandler("unmute", self.unmute_user))
        
        # Warning system
        self.app.add_handler(CommandHandler("warn", WarnModule.warn_user))
        self.app.add_handler(CommandHandler("warnlist", WarnModule.list_warnings))
        self.app.add_handler(CommandHandler("resetwarn", WarnModule.reset_warnings))
        
        # Custom commands
        self.app.add_handler(CommandHandler("addcmd", self.add_custom_command))
        self.app.add_handler(CommandHandler("delcmd", self.del_custom_command))
        self.app.add_handler(CommandHandler("listcmd", self.list_custom_commands))
        
        # Stats
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        
        # Handle custom commands
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_custom_commands))
        
        # Welcome/Goodbye messages
        self.app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, WelcomeModule.handle_new_member))
        self.app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, GoodbyeModule.handle_left_member))
        
        # Anti-link
        self.app.add_handler(MessageHandler(filters.TEXT, AntiLinkModule.check_message))
    
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
    
    parser = argparse.ArgumentParser(description='Group Manager Bot')
    parser.add_argument('--token', type=str, required=True, help='Telegram Bot Token')
    parser.add_argument('--name', type=str, default='GroupManager', help='Bot Name')
    
    args = parser.parse_args()
    
    bot = GroupManagerBot(token=args.token, bot_name=args.name)
    bot.run()


if __name__ == '__main__':
    main()
