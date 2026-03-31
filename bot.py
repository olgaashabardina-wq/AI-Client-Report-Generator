import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from utils.ai_processor import (
    process_dialog_with_ai,
    process_design_dialog_with_ai,
    process_product_card_with_ai,
)
from utils.image_generator import generate_image_from_prompt
from utils.pdf_generator import (
    generate_pdf_report,
    generate_design_pdf_report,
    generate_product_card_pdf,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp_uploads"
TEMP_DIR.mkdir(exist_ok=True)

STATE_KEY = "state"
REPORT_TYPE_KEY = "report_type"
PRODUCT_NAME_KEY = "product_name"

STATE_WAITING_TXT = "waiting_txt"
STATE_WAITING_PRODUCT_NAME = "waiting_product_name"
STATE_WAITING_PRODUCT_PRICE = "waiting_product_price"


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Создать новый отчёт", callback_data="create_report")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_report_type_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Базовый отчёт", callback_data="report_standard")],
        [InlineKeyboardButton("Дизайн сайта", callback_data="report_design")],
        [InlineKeyboardButton("Карточка товара", callback_data="report_product")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()

    text = (
        "Привет! Я помогу сгенерировать PDF-отчёт.\n\n"
        "Нажми кнопку ниже, чтобы выбрать тип отчёта."
    )

    if update.message:
        await update.message.reply_text(text, reply_markup=get_main_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            text,
            reply_markup=get_main_menu_keyboard()
        )


async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "create_report":
        context.user_data.clear()
        await query.message.reply_text(
            "Выберите тип отчёта:",
            reply_markup=get_report_type_keyboard()
        )
        return

    if callback_data == "report_standard":
        context.user_data[REPORT_TYPE_KEY] = "standard"
        context.user_data[STATE_KEY] = STATE_WAITING_TXT

        await query.message.reply_text(
            "Выбран базовый отчёт.\n"
            "Теперь отправь текстовый файл с транскрибацией диалога в формате .txt"
        )
        return

    if callback_data == "report_design":
        context.user_data[REPORT_TYPE_KEY] = "design"
        context.user_data[STATE_KEY] = STATE_WAITING_TXT

        await query.message.reply_text(
            "Выбран отчёт по заказу для генерации дизайна сайта.\n"
            "Теперь отправь текстовый файл с транскрибацией диалога в формате .txt"
        )
        return

    if callback_data == "report_product":
        context.user_data[REPORT_TYPE_KEY] = "product"
        context.user_data[STATE_KEY] = STATE_WAITING_PRODUCT_NAME

        await query.message.reply_text(
            "Выбрана карточка товара.\n"
            "Отправь название товара."
        )
        return


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    state = context.user_data.get(STATE_KEY)

    if state == STATE_WAITING_PRODUCT_NAME:
        context.user_data[PRODUCT_NAME_KEY] = text
        context.user_data[STATE_KEY] = STATE_WAITING_PRODUCT_PRICE

        await update.message.reply_text("Теперь отправь стоимость товара.")
        return

    if state == STATE_WAITING_PRODUCT_PRICE:
        product_name = context.user_data.get(PRODUCT_NAME_KEY, "").strip()
        price = text.strip()

        if not product_name:
            context.user_data[STATE_KEY] = STATE_WAITING_PRODUCT_NAME
            await update.message.reply_text(
                "Название товара не найдено. Отправь название товара ещё раз."
            )
            return

        if not price:
            await update.message.reply_text("Стоимость не должна быть пустой. Отправь стоимость товара.")
            return

        await update.message.reply_text("Генерирую карточку товара...")

        try:
            product_data = process_product_card_with_ai(product_name, price)

            image_uri = generate_image_from_prompt(
                prompt=product_data["image_prompt"],
                filename_prefix="product_card"
            )
            product_data["generated_image"] = image_uri

            pdf_path = generate_product_card_pdf(product_data)

            await update.message.reply_text("PDF готов. Отправляю файл...")
            with open(pdf_path, "rb") as pdf_file:
                await update.message.reply_document(document=pdf_file)

            await update.message.reply_text(
                "Отчёт успешно создан! Хотите создать ещё один?",
                reply_markup=get_main_menu_keyboard()
            )

            context.user_data.clear()

        except Exception as error:
            logger.exception("Ошибка при создании карточки товара: %s", error)
            await update.message.reply_text(f"Произошла ошибка: {error}")
            await update.message.reply_text(
                "Попробуйте снова.",
                reply_markup=get_main_menu_keyboard()
            )
            context.user_data.clear()

        return

    await update.message.reply_text(
        "Нажми «Создать новый отчёт», чтобы выбрать сценарий.",
        reply_markup=get_main_menu_keyboard()
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document if update.message else None

    if not document:
        return

    report_type = context.user_data.get(REPORT_TYPE_KEY)
    state = context.user_data.get(STATE_KEY)

    if state != STATE_WAITING_TXT or report_type not in {"standard", "design"}:
        await update.message.reply_text(
            "Сначала выбери тип отчёта через кнопку «Создать новый отчёт».",
            reply_markup=get_main_menu_keyboard()
        )
        return

    if not document.file_name or not document.file_name.lower().endswith(".txt"):
        await update.message.reply_text(
            "Пожалуйста, отправь текстовый файл в формате .txt"
        )
        return

    try:
        await update.message.reply_text("Файл получен. Начинаю обработку...")

        telegram_file = await context.bot.get_file(document.file_id)
        file_path = TEMP_DIR / document.file_name
        await telegram_file.download_to_drive(file_path)

        dialog_text = file_path.read_text(encoding="utf-8").strip()

        if not dialog_text:
            await update.message.reply_text("Файл пустой. Отправь файл с текстом.")
            return

        if report_type == "design":
            await update.message.reply_text("Обработка диалога с помощью ИИ...")

            design_data = process_design_dialog_with_ai(dialog_text)

            design_prompt = (
                design_data["image_prompt"]
                + ", realistic homepage website UI mockup, desktop screen, "
                  "clean corporate landing page, business website interface, "
                  "professional structure, not illustration, not poster"
            )

            await update.message.reply_text("Генерация примера дизайна сайта...")

            image_uri = generate_image_from_prompt(
                prompt=design_prompt,
                filename_prefix="bot_site_mockup"
            )
            design_data["generated_image"] = image_uri

            await update.message.reply_text("Генерация PDF-отчёта...")
            pdf_path = generate_design_pdf_report(design_data)

        else:
            await update.message.reply_text("Обработка диалога с помощью ИИ...")
            structured_data = process_dialog_with_ai(dialog_text)

            await update.message.reply_text("Генерация PDF-отчёта...")
            pdf_path = generate_pdf_report(structured_data)

        await update.message.reply_text("PDF готов. Отправляю файл...")
        with open(pdf_path, "rb") as pdf_file:
            await update.message.reply_document(document=pdf_file)

        await update.message.reply_text(
            "Отчёт успешно создан! Хотите создать ещё один?",
            reply_markup=get_main_menu_keyboard()
        )

        context.user_data.clear()

    except Exception as error:
        logger.exception("Ошибка при обработке файла: %s", error)
        await update.message.reply_text(f"Произошла ошибка: {error}")
        await update.message.reply_text(
            "Попробуйте снова.",
            reply_markup=get_main_menu_keyboard()
        )
        context.user_data.clear()


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env")

    application = (
    Application.builder()
    .token(token)
    .read_timeout(120)
    .write_timeout(120)
    .connect_timeout(120)
    .pool_timeout(120)
    .build()
)       

    application.add_handler(CommandHandler("start", handle_start_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Бот запущен")
    application.run_polling()


if __name__ == "__main__":
    main()