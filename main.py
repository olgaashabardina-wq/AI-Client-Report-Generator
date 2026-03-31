import logging
from pathlib import Path

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


BASE_DIR = Path(__file__).resolve().parent
DIALOG_FILE = BASE_DIR / "sample_dialog.txt"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "app.log"


def setup_logging() -> None:
    LOGS_DIR.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )


def read_dialog_text(file_path: Path) -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    text = file_path.read_text(encoding="utf-8").strip()

    if not text:
        raise ValueError(f"Файл пустой: {file_path}")

    return text


def choose_report_type() -> str:
    print("Выберите тип отчёта:")
    print("1 - Базовый отчёт по диалогу")
    print("2 - Отчёт по заказу дизайна сайта")
    print("3 - Карточка товара для маркетплейса")

    choice = input("Введите 1, 2 или 3: ").strip()

    if choice == "2":
        return "design"
    if choice == "3":
        return "product"
    return "standard"


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("Запуск генерации отчёта")
        report_type = choose_report_type()
        logger.info("Выбран тип отчёта: %s", report_type)

        if report_type == "standard":
            dialog_text = read_dialog_text(DIALOG_FILE)
            logger.info("Считывание диалога из файла: %s", DIALOG_FILE)

            structured_data = process_dialog_with_ai(dialog_text)
            pdf_path = generate_pdf_report(structured_data)

        elif report_type == "design":
            dialog_text = read_dialog_text(DIALOG_FILE)
            logger.info("Считывание диалога для design-отчёта из файла: %s", DIALOG_FILE)

            design_data = process_design_dialog_with_ai(dialog_text)

            image_uri = generate_image_from_prompt(
                prompt=design_data["image_prompt"],
                filename_prefix="site_mockup"
            )
            design_data["generated_image"] = image_uri

            pdf_path = generate_design_pdf_report(design_data)

        else:
            product_name = input("Введите название товара: ").strip()
            price = input("Введите стоимость товара: ").strip()

            if not product_name:
                raise ValueError("Название товара не может быть пустым.")
            if not price:
                raise ValueError("Стоимость товара не может быть пустой.")

            product_data = process_product_card_with_ai(product_name, price)

            image_uri = generate_image_from_prompt(
                prompt=product_data["image_prompt"],
                filename_prefix="product_card"
            )
            product_data["generated_image"] = image_uri

            pdf_path = generate_product_card_pdf(product_data)

        logger.info("Отчёт успешно создан: %s", pdf_path)
        print(f"Отчёт успешно создан: {pdf_path}")

    except FileNotFoundError as error:
        logger.exception("Ошибка файла")
        print(f"Ошибка: {error}")

    except ValueError as error:
        logger.exception("Ошибка данных")
        print(f"Ошибка: {error}")

    except Exception as error:
        logger.exception("Непредвиденная ошибка")
        print(f"Произошла ошибка: {error}")


if __name__ == "__main__":
    main()