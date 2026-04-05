import csv
import io
from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from app.models import Article


COLUMNS = [
    ("Название", "title"),
    ("Авторы", "authors"),
    ("DOI", "doi"),
    ("Дата публикации", "published_at"),
    ("Журнал / Издание", "journal_name"),
    ("ISSN", "issn"),
    ("Тип", "type"),
    ("Квартиль", "quartile"),
    ("Белый список МОН", "white_list_level"),
    ("CORE Rank", "core_rank"),
    ("В Scopus", "in_scopus"),
    ("Издатель", "publisher"),
    ("Цитирования", "cited_by_count"),
    ("Язык", "language"),
    ("Источник", "source"),
    ("Темы", "topics"),
]


def _cell_value(article: Article, field: str):
    val = getattr(article, field, None)
    if val is None:
        return ""
    if isinstance(val, bool):
        return "Да" if val else "Нет"
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    return val


def export_xlsx(articles: list[Article]) -> io.BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Публикации"

    headers = [c[0] for c in COLUMNS]
    ws.append(headers)
    bold = Font(bold=True)
    for cell in ws[1]:
        cell.font = bold
        cell.alignment = Alignment(horizontal="center")

    for article in articles:
        ws.append([_cell_value(article, c[1]) for c in COLUMNS])

    for col in ws.columns:
        max_len = 0
        for cell in col:
            try:
                max_len = max(max_len, len(str(cell.value or "")))
            except Exception:
                pass
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def export_csv(articles: list[Article]) -> io.StringIO:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([c[0] for c in COLUMNS])
    for article in articles:
        writer.writerow([_cell_value(article, c[1]) for c in COLUMNS])
    buf.seek(0)
    return buf
