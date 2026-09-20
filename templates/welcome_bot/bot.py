import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s [%(name)s] %(message)s', level=logging.INFO)

TOKEN = os.getenv('BOT_TOKEN')
BOT_ID = os.getenv('BOT_ID', 'Unknown')

# Pesan welcome default (bisa diubah via /setwelcome)
welcome_messages = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f'Welcome Bot ({BOT_ID}) aktif!\n'
        f'Tambahkan saya ke grup untuk menyambut member baru.\n\n'
        f'/setwelcome <pesan> - Ubah pesan welcome'
    )

async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Gunakan: /setwelcome Selamat datang {name}!')
        return
    chat_id = update.effective_chat.id
    welcome_messages[chat_id] = ' '.join(context.args)
    await update.message.reply_text('Pesan welcome berhasil diubah!')

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        chat_id = update.effective_chat.id
        msg = welcome_messages.get(chat_id, 'Selamat datang {name}!')
        await update.message.reply_text(msg.replace('{name}', member.first_name))

def main():
    print(f"[{BOT_ID}] Welcome Bot starting...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setwelcome", set_welcome))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    print(f"[{BOT_ID}] Welcome Bot running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()