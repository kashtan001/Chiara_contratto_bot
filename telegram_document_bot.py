# telegram_document_bot.py — Упрощенный бот для генерации contratto
# -----------------------------------------------------------------------------
# Генератор PDF-документа:
#   contratto — договор о предоставлении услуг консультирования и инвестирования
# -----------------------------------------------------------------------------
# Зависимости:
#   pip install python-telegram-bot==20.* reportlab
# -----------------------------------------------------------------------------
import logging
import os
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP

from telegram import Update, InputFile, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, ConversationHandler, MessageHandler, ContextTypes, filters,
)

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

# ---------------------- Настройки ------------------------------------------
TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
LOGO_PATH = "image1.png"      # логотип 
SIGNATURE_PATH = "image2.png"      # подпись 
SMALL_LOGO_PATH = "image3.png"     # маленький значок слева от подписи

logging.basicConfig(format="%(asctime)s — %(levelname)s — %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------ Состояния Conversation -------------------------------
ASK_NAME, ASK_AMOUNT = range(2)

# ---------------------- Утилиты -------------------------------------------
def money(val: float) -> str:
    """Формат суммы: € 0.00"""
    return f"€ {Decimal(val).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Header", alignment=TA_CENTER, fontSize=14, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Body", fontSize=11, leading=15))
    return styles

# ---------------------- PDF-строители --------------------------------------
def build_contratto(data: dict) -> BytesIO:
    from datetime import datetime
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Flowable
    
    buf = BytesIO()
    s = _styles()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    elems = []
    
    # --- Функция для вставки логотипа ---
    def draw_logo(canvas, doc):
        try:
            if os.path.exists(LOGO_PATH):
                from reportlab.lib.utils import ImageReader
                logo = ImageReader(LOGO_PATH)
                # Сохраняем пропорции изображения
                iw, ih = logo.getSize()
                aspect = (iw / ih) if ih else 1.0
                desired_h = 3.2*cm
                logo_height = desired_h
                logo_width = desired_h * aspect
                # По центру сверху
                x = (A4[0] - logo_width) / 2
                y = A4[1] - 2*cm - logo_height
                canvas.drawImage(logo, x, y, width=logo_width, height=logo_height, mask='auto')
        except Exception as e:
            print(f"Ошибка вставки логотипа: {e}")
    
    # Заголовок документа
    elems.append(Spacer(1, 3.5*cm))  # Отступ под логотип
    elems.append(Paragraph('<b>Contratto di prestazione di servizi di consulenza e investimento</b>', 
                          ParagraphStyle('Title', parent=s["Header"], fontSize=16, spaceAfter=20, fontName="Helvetica-Bold")))
    
    # 1. Parti e oggetto del contratto
    elems.append(Paragraph('<b>1. Parti e oggetto del contratto</b>', s["Header"]))
    elems.append(Spacer(1, 8))
    
    contract_text1 = (f"Il presente contratto è stipulato tra Chiara Lombardi (di seguito – «Fornitore») e "
                     f"<b>{data['name']}</b> (di seguito – «Cliente»).")
    elems.append(Paragraph(contract_text1, s["Body"]))
    elems.append(Spacer(1, 8))
    
    contract_text2 = ("Il Fornitore si impegna a fornire al Cliente servizi di consulenza e investimento "
                      "nel settore delle criptovalute utilizzando le proprie strategie, e il Cliente si impegna "
                      "a versare l'investimento e a corrispondere il compenso secondo le condizioni del presente contratto.")
    elems.append(Paragraph(contract_text2, s["Body"]))
    elems.append(Spacer(1, 16))
    
    # 2. Legislazione applicabile
    elems.append(Paragraph('<b>2. Legislazione applicabile</b>', s["Header"]))
    elems.append(Spacer(1, 8))
    
    leg_text1 = ("2.1. Il presente contratto è regolato dalle norme del Codice Civile italiano (Codice Civile), "
                "che disciplina i rapporti civili e commerciali in Italia.")
    elems.append(Paragraph(leg_text1, s["Body"]))
    elems.append(Spacer(1, 8))
    
    leg_text2 = ("2.2. Le parti hanno diritto di scegliere la legge applicabile al contratto in conformità "
                "al Regolamento CE «Roma I» (Rome I Regulation), che garantisce la libertà di scelta della legge "
                "nei rapporti contrattuali nell'Unione Europea.")
    elems.append(Paragraph(leg_text2, s["Body"]))
    elems.append(Spacer(1, 8))
    
    leg_text3 = ("2.3. L'attività relativa ai servizi di investimento e finanziari è soggetta alla vigilanza "
                "della Commissione Nazionale per le Società e la Borsa (CONSOB), nonché al Regolamento della "
                "Banca d'Italia e della CONSOB del 29 ottobre 2007 «Regolamento sull'organizzazione e sulle "
                "procedure di prestazione dei servizi di investimento e collettivi».")
    elems.append(Paragraph(leg_text3, s["Body"]))
    elems.append(Spacer(1, 16))
    
    # 3. Trasparenza e garanzie di fiducia
    elems.append(Paragraph('<b>3. Trasparenza e garanzie di fiducia</b>', s["Header"]))
    elems.append(Spacer(1, 8))
    
    trasp_text1 = ("3.1. Il Fornitore fornisce al Cliente prove dell'efficacia del proprio lavoro: "
                   "testimonianze, risultati dei clienti, materiali di supporto.")
    elems.append(Paragraph(trasp_text1, s["Body"]))
    elems.append(Spacer(1, 8))
    
    trasp_text2 = ("3.2. Su richiesta del Cliente, il Fornitore può fornire anche documenti personali "
                   "che attestino la propria identità e il proprio status legale.")
    elems.append(Paragraph(trasp_text2, s["Body"]))
    elems.append(Spacer(1, 8))
    
    trasp_text3 = ("3.3. Il Fornitore è partner ufficiale dell'exchange Bitget, fatto che conferma "
                   "ulteriormente il suo status professionale e il livello di affidabilità.")
    elems.append(Paragraph(trasp_text3, s["Body"]))
    elems.append(Spacer(1, 16))
    
    # 4. Validità giuridica del contratto
    elems.append(Paragraph('<b>4. Validità giuridica del contratto</b>', s["Header"]))
    elems.append(Spacer(1, 8))
    
    val_text1 = ("4.1. Il contratto è redatto in forma scritta e firmato da entrambe le parti. "
                "Ha piena validità giuridica sul territorio italiano in conformità alle norme del Codice Civile italiano.")
    elems.append(Paragraph(val_text1, s["Body"]))
    elems.append(Spacer(1, 8))
    
    val_text2 = ("4.2. In caso di controversie, le parti si impegnano a tentare una risoluzione amichevole. "
                "Qualora non fosse possibile, le controversie saranno deferite al tribunale competente in Italia "
                "o ad arbitrato, se previsto dal contratto, in conformità al Regolamento Roma I.")
    elems.append(Paragraph(val_text2, s["Body"]))
    elems.append(Spacer(1, 16))
    
    # 5. Durata e responsabilità
    elems.append(Paragraph('<b>5. Durata e responsabilità</b>', s["Header"]))
    elems.append(Spacer(1, 8))
    
    dur_text1 = ("5.1. Il contratto entra in vigore al momento della firma da parte di entrambe le parti "
                "e rimane valido fino al completo adempimento degli obblighi.")
    elems.append(Paragraph(dur_text1, s["Body"]))
    elems.append(Spacer(1, 8))
    
    dur_text2 = ("5.2. Le parti sono responsabili per la violazione delle condizioni contrattuali "
                "in conformità alla legislazione vigente in Italia.")
    elems.append(Paragraph(dur_text2, s["Body"]))
    elems.append(Spacer(1, 16))
    
    # 6. Importo dell'investimento
    elems.append(Paragraph('<b>6. Importo dell\'investimento</b>', s["Header"]))
    elems.append(Spacer(1, 8))
    
    amount_text = f"6.1. Il Cliente versa un investimento pari a:<br/><b>{money(data['amount'])} (l'importo viene indicato al momento della firma del contratto).</b>"
    elems.append(Paragraph(amount_text, s["Body"]))
    elems.append(Spacer(1, 8))
    
    inv_text2 = ("6.2. L'importo viene utilizzato nell'ambito dei servizi forniti secondo il presente contratto.")
    elems.append(Paragraph(inv_text2, s["Body"]))
    elems.append(Spacer(1, 8))
    
    inv_text3 = ("6.3. Il Fornitore conferma la ricezione dell'importo e si impegna a lavorare "
                "nell'interesse del Cliente in conformità al presente contratto.")
    elems.append(Paragraph(inv_text3, s["Body"]))
    elems.append(Spacer(1, 24))
    
    # 7. Firme delle parti
    elems.append(Paragraph('<b>7. Firme delle parti</b>', s["Header"]))
    elems.append(Spacer(1, 16))
    
    # Класс для линий подписи
    class SignatureLine(Flowable):
        def __init__(self, label, width, sign_path=None, sign_width=None, sign_height=None, 
                     fontname="Helvetica", fontsize=11, left_icon_path=None, left_icon_width=None, left_icon_height=None):
            super().__init__()
            self.label = label
            self.width = width
            self.sign_path = sign_path
            self.sign_width = sign_width
            self.sign_height = sign_height
            self.left_icon_path = left_icon_path
            self.left_icon_width = left_icon_width
            self.left_icon_height = left_icon_height
            self.fontname = fontname
            self.fontsize = fontsize
            self.height = max(1.2*fontsize, (sign_height if sign_height else 0.5*cm))
            
        def draw(self):
            c = self.canv
            c.saveState()
            c.setFont(self.fontname, self.fontsize)
            text_width = c.stringWidth(self.label, self.fontname, self.fontsize)
            y = 0
            
            # Нарисовать текст
            c.drawString(0, y, self.label)
            
            # Нарисовать линию после текста
            line_x0 = text_width + 6
            line_x1 = self.width
            c.setLineWidth(1)
            c.line(line_x0, y, line_x1, y)
            
            # Если есть картинка подписи — по центру линии
            if self.sign_path and os.path.exists(self.sign_path):
                from reportlab.lib.utils import ImageReader
                img = ImageReader(self.sign_path)
                line_len = line_x1 - line_x0
                img_x = line_x0 + (line_len - self.sign_width) / 2
                img_y = y - self.sign_height/2
                c.drawImage(img, img_x, img_y, width=self.sign_width, height=self.sign_height, mask='auto')
                
                # Дополнительный значок Bitget справа
                if self.left_icon_path and os.path.exists(self.left_icon_path) and self.left_icon_height:
                    try:
                        right_margin = 0.5*cm
                        vertical_offset = 0.45*cm
                        left_img = ImageReader(self.left_icon_path)
                        iw, ih = left_img.getSize()
                        aspect = (iw / ih) if ih else 1.0
                        final_h = self.left_icon_height
                        final_w = final_h * aspect
                        icon_x = line_x1 - right_margin - final_w
                        icon_y = y - final_h/2 + vertical_offset
                        c.drawImage(left_img, icon_x, icon_y, width=final_w, height=final_h, mask='auto')
                    except Exception:
                        pass
            c.restoreState()
    
    # Ширина всей строки
    line_width = A4[0] - 2*cm*2
    
    # Подпись поставщика
    elems.append(SignatureLine(
        label="Fornitore: Chiara Lombardi ",
        width=line_width,
        sign_path=SIGNATURE_PATH,
        sign_width=4*cm,
        sign_height=1.5*cm,
        fontname="Helvetica",
        fontsize=11,
        left_icon_path=SMALL_LOGO_PATH,
        left_icon_width=1.4*cm,
        left_icon_height=1.4*cm
    ))
    elems.append(Spacer(1, 24))
    
    # Подпись клиента
    elems.append(SignatureLine(
        label="Cliente: ",
        width=line_width,
        sign_path=None,
        fontname="Helvetica",
        fontsize=11
    ))
    
    try:
        doc.build(elems, onFirstPage=draw_logo, onLaterPages=draw_logo)
    except Exception as pdf_err:
        print(f"Ошибка генерации PDF: {pdf_err}")
        raise
    
    buf.seek(0)
    return buf



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
        amt = float(update.message.text.replace('€','').replace(',','.'))
    except:
        await update.message.reply_text("Importo non valido, riprova:")
        return ASK_AMOUNT
    
    context.user_data['amount'] = round(amt, 2)
    d = context.user_data
    
    try:
        buf = build_contratto(d)
        filename = f"Contratto_{d['name']}.pdf"
    except Exception as e:
        print(f"Ошибка при формировании PDF: {e}")
        await update.message.reply_text("Ошибка при формировании PDF. Сообщите администратору.")
        return ConversationHandler.END
    
    try:
        await update.message.reply_document(InputFile(buf, filename))
    except Exception as send_err:
        print(f"Ошибка отправки PDF: {send_err}")
        await update.message.reply_text("Ошибка при отправке PDF. Сообщите администратору.")
        return ConversationHandler.END
    
    return await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operazione annullata.")
    return await start(update, context)

# ---------------------------- Main -------------------------------------------
def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_NAME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)],
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == '__main__':
    main()

