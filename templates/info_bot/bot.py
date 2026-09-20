import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(format='%(asctime)s [%(name)s] %(message)s', level=logging.INFO)

TOKEN = os.getenv('BOT_TOKEN')
BOT_ID = os.getenv('BOT_ID', 'Unknown')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f'Info Bot ({BOT_ID})\n\n'
        f'/info - Lihat info lengkap Anda\n'
        f'/id - Lihat User ID Anda'
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    text = (
        f"--- User Info ---\n"
        f"Nama: {user.full_name}\n"
        f"Username: @{user.username or 'Tidak ada'}\n"
        f"User ID: {user.id}\n"
        f"Bahasa: {user.language_code or 'Unknown'}\n"
        f"Premium: {'Ya' if user.is_premium else 'Tidak'}\n\n"
        f"--- Chat Info ---\n"
        f"Chat ID: {chat.id}\n"
        f"Tipe: {chat.type}"
    )
    await update.message.reply_text(text)

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'User ID Anda: {update.effective_user.id}')

def main():
    print(f"[{BOT_ID}] Info Bot starting...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("id", get_id))
    print(f"[{BOT_ID}] Info Bot running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()