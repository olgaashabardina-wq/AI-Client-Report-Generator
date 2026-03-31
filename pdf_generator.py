import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
REPORTS_DIR = BASE_DIR / "reports"


def get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"])
    )


def _render_pdf(template_name: str, data: dict, filename_prefix: str) -> str:
    REPORTS_DIR.mkdir(exist_ok=True)

    env = get_jinja_env()
    template = env.get_template(template_name)

    if "dialog_date" in data and not data["dialog_date"]:
        data["dialog_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    html_content = template.render(data=data)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_path = REPORTS_DIR / f"{filename_prefix}_{timestamp}.pdf"

    HTML(string=html_content, base_url=str(BASE_DIR)).write_pdf(output_path)

    logger.info("PDF успешно сохранён: %s", output_path)
    return str(output_path)


def generate_pdf_report(data: dict) -> str:
    return _render_pdf("report_template.html", data, "report")


def generate_design_pdf_report(data: dict) -> str:
    return _render_pdf("design_report_template.html", data, "design_report")


def generate_product_card_pdf(data: dict) -> str:
    return _render_pdf("product_card_template.html", data, "product_card")