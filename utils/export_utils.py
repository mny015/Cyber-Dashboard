import csv
import json
from datetime import date, datetime
from io import BytesIO, StringIO
from zipfile import ZIP_DEFLATED, ZipFile


def json_bytes(data):
    content = json.dumps(data, default=_json_value, indent=2, ensure_ascii=True)
    return BytesIO(content.encode("utf-8"))


def csv_zip_bytes(sections):
    archive_buffer = BytesIO()
    with ZipFile(archive_buffer, "w", ZIP_DEFLATED) as archive:
        for section_name, rows in sections.items():
            text_buffer = StringIO(newline="")
            fieldnames = _fieldnames(rows)
            writer = csv.DictWriter(text_buffer, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})
            archive.writestr(f"{section_name}.csv", text_buffer.getvalue())
    archive_buffer.seek(0)
    return archive_buffer


def export_filename(scope, extension):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"cyber-dashboard-{scope}-{timestamp}.{extension}"


def _fieldnames(rows):
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    return fields or ["message"]


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Cannot export value of type {type(value).__name__}")


def _csv_value(value):
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        value = value.isoformat()
    value = str(value)
    if value.startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value
