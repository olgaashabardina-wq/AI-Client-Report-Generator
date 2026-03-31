import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)


def _clean_json_response(content: str) -> str:
    content = content.strip()

    if content.startswith("```json"):
        content = content.removeprefix("```json").strip()
    if content.startswith("```"):
        content = content.removeprefix("```").strip()
    if content.endswith("```"):
        content = content.removesuffix("```").strip()

    return content


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise ValueError("OPENAI_API_KEY не найден в .env")
    return OpenAI(api_key=api_key)


def get_mock_design_data() -> dict:
    return {
        "client_name": "Иван Петров",
        "client_company": "Айсберг",
        "project_type": "Дизайн главной страницы корпоративного сайта",
        "style_preferences": "Современный минималистичный корпоративный стиль, светлый фон, сине-голубые акценты, строгая деловая подача",
        "target_audience": "B2B-клиенты, руководители предприятий, технические специалисты, партнёры",
        "pages": "Главная страница, услуги, о компании, кейсы, контакты",
        "required_blocks": "Первый экран, о компании, услуги, преимущества, кейсы, форма обратной связи, контакты",
        "deadline": "1 месяц",
        "budget": "200000–250000 руб.",
        "mood": "Позитивное",
        "image_prompt": (
            "Website homepage design for Iceberg company, corporate B2B website, "
            "industrial refrigeration equipment business, clean modern landing page, "
            "light background, blue and cyan accents, professional business style, "
            "hero section with headline and CTA button, company services section, "
            "about company block, advantages, case studies preview, contact form, "
            "structured corporate homepage UI, realistic website mockup, desktop view, "
            "NOT ecommerce, NOT clothing, NOT fashion, NOT online store, NOT marketplace"
        )
    }


def get_mock_data() -> dict:
    return {
        "client_name": "Иван Петров",
        "client_company": "Айсберг",
        "client_position": "Представитель компании",
        "dialog_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "manager_name": "Анна Смирнова",
        "topic": "Разработка корпоративного сайта",
        "main_request": "Создание нового корпоративного сайта для компании",
        "business_goal": "Улучшить онлайн-присутствие и увеличить количество заявок",
        "budget": "200000–250000 руб.",
        "deadline": "1 месяц",
        "target_audience": "B2B-клиенты и потенциальные партнёры",
        "pain_points": "Устаревший сайт, неудобный интерфейс, низкая конверсия",
        "required_features": "Главная, услуги, о компании, контакты, форма обратной связи, мобильная адаптация, блог, CRM",
        "mood": "Позитивное",
        "next_steps": [
            "Подготовить коммерческое предложение",
            "Отправить примеры работ клиенту",
            "Согласовать следующую встречу"
        ]
    }


def get_mock_product_data(product_name: str, price: str) -> dict:
    return {
        "product_name": product_name,
        "price": price,
        "description": (
            f"{product_name} сохраняет температуру напитков и подходит для повседневного использования. "
            f"Практичный дизайн и аккуратный внешний вид делают товар удобным для дома, офиса и поездок."
        ),
        "image_prompt": (
            f"Marketplace product photo for {product_name}, premium thermos mug, realistic product photography, "
            f"warm cafe background, soft bokeh lights, stylish composition, ecommerce product image, brand Iceberg"
        )
    }


def process_dialog_with_ai(text: str) -> dict:
    try:
        client = get_client()
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        prompt = f"""
Извлеки из диалога структурированные данные.
Верни только валидный JSON без пояснений.

Формат:
{{
  "client_name": "...",
  "client_company": "...",
  "client_position": "...",
  "dialog_date": "...",
  "manager_name": "...",
  "topic": "...",
  "main_request": "...",
  "business_goal": "...",
  "budget": "...",
  "deadline": "...",
  "target_audience": "...",
  "pain_points": "...",
  "required_features": "...",
  "mood": "...",
  "next_steps": ["...", "...", "..."]
}}

Диалог:
{text}
"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Ты извлекаешь данные из диалога и возвращаешь только валидный JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content or ""
        content = _clean_json_response(content)

        return json.loads(content)

    except Exception as error:
        logger.exception("Ошибка при обработке базового отчёта: %s", error)
        logger.warning("Возвращаются mock-данные для базового отчёта.")
        return get_mock_data()


def process_design_dialog_with_ai(text: str) -> dict:
    try:
        client = get_client()
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        prompt = f"""
Проанализируй диалог и верни только валидный JSON без пояснений.

Это отчёт по заказу для генерации дизайна сайта.
Нужно получить данные для PDF-отчёта и отдельно составить image_prompt
для генерации примера дизайна ГЛАВНОЙ СТРАНИЦЫ сайта.

Важно:
- компания называется "Айсберг"
- это корпоративный B2B-сайт
- компания занимается поставкой, монтажом и обслуживанием промышленного холодильного оборудования
- нужен НЕ интернет-магазин
- нужен НЕ fashion-style
- нужен НЕ marketplace
- нужен НЕ каталог одежды
- нужен именно макет homepage / landing page корпоративного сайта

В image_prompt обязательно укажи:
- corporate website homepage
- industrial refrigeration equipment company
- modern business layout
- light background
- blue and cyan accents
- hero section
- services block
- about company block
- advantages
- cases preview
- contact form
- desktop website mockup

Формат JSON:
{{
  "client_name": "...",
  "client_company": "Айсберг",
  "project_type": "...",
  "style_preferences": "...",
  "target_audience": "...",
  "pages": "...",
  "required_blocks": "...",
  "deadline": "...",
  "budget": "...",
  "mood": "...",
  "image_prompt": "..."
}}

Диалог:
{text}
"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты возвращаешь только валидный JSON. "
                        "image_prompt должен описывать realistic homepage website UI mockup "
                        "для корпоративного B2B-сайта компании Айсберг. "
                        "Запрещено уходить в ecommerce, fashion, clothing, marketplace, catalog store."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content or ""
        content = _clean_json_response(content)

        data = json.loads(content)
        data["client_company"] = "Айсберг"

        return data

    except Exception as error:
        logger.exception("Ошибка при обработке design-отчёта: %s", error)
        logger.warning("Возвращаются mock-данные для design-отчёта.")
        return get_mock_design_data()


def process_product_card_with_ai(product_name: str, price: str) -> dict:
    try:
        client = get_client()
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        prompt = f"""
Создай данные для карточки товара маркетплейса.
Верни только валидный JSON без пояснений.

Название товара: {product_name}
Стоимость: {price}

Формат:
{{
  "product_name": "{product_name}",
  "price": "{price}",
  "description": "...",
  "image_prompt": "..."
}}

Требования:
- description: 2-3 предложения, понятное описание товара
- image_prompt: подробный промпт на английском для генерации красивого товарного изображения
"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Ты создаёшь JSON для карточки товара и возвращаешь только валидный JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )

        content = response.choices[0].message.content or ""
        content = _clean_json_response(content)

        return json.loads(content)

    except Exception as error:
        logger.exception("Ошибка при генерации карточки товара: %s", error)
        logger.warning("Возвращаются mock-данные для карточки товара.")
        return get_mock_product_data(product_name, price)

