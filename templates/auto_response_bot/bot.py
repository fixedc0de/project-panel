"""
Auto Response Bot - Template Bot Telegram untuk Auto-Response Berbasis Keyword
"""

import os
import sys
import re
import sqlite3
from typing import Optional
import logging

logging.basicConfig(format='%(asctime)s [%(name)s] %(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    logger.info("Installing python-telegram-bot...")
    os.system("pip install python-telegram-bot==21.0")
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


class AutoResponseDB:
    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        db_path = os.path.join(os.path.dirname(__file__), f'{bot_id}.db')
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.init_db()
    
    def init_db(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS auto_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT, keyword TEXT NOT NULL, response TEXT NOT NULL,
            enabled INTEGER DEFAULT 1, use_regex INTEGER DEFAULT 0,
            UNIQUE(chat_id, keyword))''')
        self.conn.commit()
    
    def add_response(self, chat_id: str, keyword: str, response: str, use_regex: bool = False):
        self.cursor.execute('INSERT OR REPLACE INTO auto_responses (chat_id, keyword, response, use_regex) VALUES (?, ?, ?, ?)',
                          (chat_id, keyword.lower(), response, 1 if use_regex else 0))
        self.conn.commit()
    
    def delete_response(self, chat_id: str, keyword: str):
        self.cursor.execute('DELETE FROM auto_responses WHERE chat_id = ? AND keyword = ?', (chat_id, keyword.lower()))
        self.conn.commit()
    
    def get_response(self, chat_id: str, text: str) -> Optional[str]:
        text_lower = text.lower()
        self.cursor.execute('SELECT response FROM auto_responses WHERE chat_id = ? AND keyword = ? AND enabled = 1 AND use_regex = 0',
                          (chat_id, text_lower))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        self.cursor.execute('SELECT keyword, response FROM auto_responses WHERE chat_id = ? AND enabled = 1 AND use_regex = 1', (chat_id,))
        for row in self.cursor.fetchall():
            try:
                if re.search(row[0], text, re.IGNORECASE):
                    return row[1]
            except re.error:
                continue
        return None
    
    def list_responses(self, chat_id: str) -> list:
        self.cursor.execute('SELECT keyword, response, enabled FROM auto_responses WHERE chat_id = ?', (chat_id,))
        return self.cursor.fetchall()
    
    def get_stats(self, chat_id: str) -> dict:
        self.cursor.execute('SELECT COUNT(*) FROM auto_responses WHERE chat_id = ?', (chat_id,))
        return {'total': self.cursor.fetchone()[0]}


class AutoResponseBot:
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        self.bot_id = os.getenv('BOT_ID', 'auto_response')
        if not self.token:
            print("ERROR: BOT_TOKEN tidak ditemukan!")
            sys.exit(1)
        
        self.db = AutoResponseDB(self.bot_id)
        self.app = Application.builder().token(self.token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("addresponse", self.cmd_addresponse))
        self.app.add_handler(CommandHandler("delresponse", self.cmd_delresponse))
        self.app.add_handler(CommandHandler("listresponse", self.cmd_listresponse))
        self.app.add_handler(CommandHandler("stats", self.cmd_stats))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_response))
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("👋 Halo! Saya Auto Response Bot. Gunakan /help untuk perintah.")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("""
📋 **COMMANDS:**
/addresponse <keyword> <response> - Tambah response
/delresponse <keyword> - Hapus response
/listresponse - List responses
/stats - Statistik
""")
    
    async def cmd_addresponse(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Gunakan: /addresponse <keyword> <response>")
            return
        keyword, response = context.args[0], ' '.join(context.args[1:])
        self.db.add_response(str(update.effective_chat.id), keyword, response)
        await update.message.reply_text(f"✅ Response '{keyword}' ditambahkan!")
    
    async def cmd_delresponse(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Gunakan: /delresponse <keyword>")
            return
        self.db.delete_response(str(update.effective_chat.id), context.args[0])
        await update.message.reply_text("✅ Dihapus!")
    
    async def cmd_listresponse(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        responses = self.db.list_responses(str(update.effective_chat.id))
        if not responses:
            await update.message.reply_text("Belum ada response.")
            return
        msg = "\n".join([f"- {r[0]}: {r[1][:30]}" for r in responses[:10]])
        await update.message.reply_text(f"📝 Responses:\n{msg}")
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        stats = self.db.get_stats(str(update.effective_chat.id))
        await update.message.reply_text(f"📊 Total: {stats['total']} responses")
    
    async def handle_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        response = self.db.get_response(str(update.effective_chat.id), update.message.text)
        if response:
            await update.message.reply_text(response)
    
    def run(self):
        print(f"[{self.bot_id}] Auto Response Bot running!")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    AutoResponseBot().run()
