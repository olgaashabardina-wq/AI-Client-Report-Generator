import base64
import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "generated_images"


def generate_image_from_prompt(prompt: str, filename_prefix: str = "image") -> str:
    IMAGES_DIR.mkdir(exist_ok=True)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        logger.warning("OPENAI_API_KEY не найден. Изображение не будет сгенерировано.")
        return ""

    try:
        client = OpenAI(api_key=api_key)

        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        filename = f"{filename_prefix}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
        image_path = IMAGES_DIR / filename

        with open(image_path, "wb") as file:
            file.write(image_bytes)

        logger.info("Изображение сохранено: %s", image_path)
        return image_path.resolve().as_uri()

    except Exception as error:
        logger.exception("Ошибка генерации изображения: %s", error)
        return ""