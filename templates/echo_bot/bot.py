import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s [%(name)s] %(message)s', level=logging.INFO)

TOKEN = os.getenv('BOT_TOKEN')
BOT_ID = os.getenv('BOT_ID', 'Unknown')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f'Halo! Saya Echo Bot ({BOT_ID}).\n'
        f'Kirim pesan apapun, saya akan membalasnya!'
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('/start - Mulai\n/help - Bantuan')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

def main():
    print(f"[{BOT_ID}] Echo Bot starting...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    print(f"[{BOT_ID}] Echo Bot running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()