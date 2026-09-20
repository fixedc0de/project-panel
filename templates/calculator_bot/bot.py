import os
import re
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(format='%(asctime)s [%(name)s] %(message)s', level=logging.INFO)

TOKEN = os.getenv('BOT_TOKEN')
BOT_ID = os.getenv('BOT_ID', 'Unknown')

def safe_calculate(expression):
    # Hanya izinkan angka, operator dasar, titik, kurung, dan spasi
    if not re.match(r'^[\d\+\-\*\/\.\(\)\s\%]+$', expression):
        return "Error: Karakter tidak valid!"
    if len(expression) > 200:
        return "Error: Ekspresi terlalu panjang!"
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except ZeroDivisionError:
        return "Error: Tidak bisa dibagi nol!"
    except Exception:
        return "Error: Ekspresi tidak valid!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f'Calculator Bot ({BOT_ID})\n\n'
        f'Gunakan: /calc <ekspresi>\n\n'
        f'Contoh:\n'
        f'/calc 2 + 2\n'
        f'/calc (10 * 5) / 2\n'
        f'/calc 100 % 3'
    )

async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Gunakan: /calc 2 + 2')
        return
    expression = ' '.join(context.args)
    result = safe_calculate(expression)
    await update.message.reply_text(f'{expression} = {result}')

def main():
    print(f"[{BOT_ID}] Calculator Bot starting...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("calc", calc))
    print(f"[{BOT_ID}] Calculator Bot running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()