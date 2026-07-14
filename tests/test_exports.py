"""Backup serialization must remain portable and spreadsheet-safe."""

import json
from datetime import date, datetime
from zipfile import ZipFile

from app.utils.exports import csv_zip_bytes, export_filename, json_bytes


def test_json_export_serializes_dates_as_utf8_iso_values():
    payload = json.loads(
        json_bytes(
            {
                "created": datetime(2026, 7, 14, 10, 30),
                "review_date": date(2026, 7, 15),
            }
        ).getvalue()
    )

    assert payload == {
        "created": "2026-07-14T10:30:00",
        "review_date": "2026-07-15",
    }


def test_csv_export_neutralizes_spreadsheet_formulas():
    archive = csv_zip_bytes(
        {"contacts": [{"name": "=HYPERLINK(\"bad\")", "email": "safe@example.com"}]}
    )

    with ZipFile(archive) as zip_file:
        csv_text = zip_file.read("contacts.csv").decode("utf-8")

    assert "'=HYPERLINK" in csv_text
    assert "safe@example.com" in csv_text


def test_export_filename_is_deterministic_when_clock_is_supplied():
    filename = export_filename("personal", "json", datetime(2026, 7, 14, 9, 5, 2))

    assert filename == "cyber-dashboard-personal-20260714-090502.json"
