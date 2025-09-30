 # telegram_document_bot.py — Telegram бот с интеграцией PDF конструктора
# -----------------------------------------------------------------------------
# Генератор PDF-документов Intesa Sanpaolo:
#   /contratto — кредитный договор
#   /garanzia  — письмо о гарантийном взносе
#   /carta     — письмо о выпуске карты
# -----------------------------------------------------------------------------
# Интеграция с pdf_costructor.py API
# -----------------------------------------------------------------------------
import logging
import os
from io import BytesIO

from telegram import Update, InputFile, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, ConversationHandler, MessageHandler, ContextTypes, filters,
)

# Импортируем API функции из PDF конструктора
from pdf_costructor import (
    generate_contratto_pdf,
    monthly_payment,
)


# ---------------------- Настройки ------------------------------------------
TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
DEFAULT_TAN = 7.86
DEFAULT_TAEG = 8.30


logging.basicConfig(format="%(asctime)s — %(levelname)s — %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------ Состояния Conversation -------------------------------
ASK_NAME, ASK_AMOUNT = range(2)

# ---------------------- PDF-строители через API -------------------------
def build_contratto(data: dict) -> BytesIO:
    """Генерация PDF договора через API pdf_costructor"""
    return generate_contratto_pdf(data)


# ------------------------- Handlers -----------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Benvenuto! Inserisci nome e cognome del cliente:",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    context.user_data['name'] = name
    await update.message.reply_text("Inserisci importo (€):")
    return ASK_AMOUNT

async def ask_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amt = float(update.message.text.replace('€','').replace(',','.').replace(' ',''))
    except:
        await update.message.reply_text("Importo non valido, riprova:")
        return ASK_AMOUNT
    context.user_data['amount'] = round(amt, 2)
    
    # Устанавливаем значения по умолчанию для остальных параметров
    context.user_data['duration'] = 36  # 36 месяцев по умолчанию
    context.user_data['tan'] = DEFAULT_TAN
    context.user_data['taeg'] = DEFAULT_TAEG
    context.user_data['payment'] = monthly_payment(amt, 36, DEFAULT_TAN)
    
    # Сразу генерируем и отправляем документ
    try:
        pdf_buffer = build_contratto(context.user_data)
        filename = f"Contrato_{context.user_data['name'].replace(' ', '_')}.pdf"
        await update.message.reply_document(
            document=InputFile(pdf_buffer, filename=filename)
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    
    return ConversationHandler.END

# Удалены неиспользуемые функции ask_duration, ask_tan, ask_taeg

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operazione annullata.")
    return await start(update, context)

# ---------------------------- Main -------------------------------------------
def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_NAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_AMOUNT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)],
    )
    app.add_handler(conv)
    
    print("🤖 Телеграм бот запущен!")
    print("📋 Генерируется: contratto")
    print("🔧 Использует PDF конструктор из pdf_costructor.py")
    
    app.run_polling()

if __name__ == '__main__':
    main()
