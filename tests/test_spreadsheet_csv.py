import csv
import io
import json
import runpy
import time
import urllib.request

from leadsniper import export_leads


def test_export_neutralizes_formula_cells_and_preserves_raw_json(tmp_path):
    leads = [
        {
            "=header": "=first",
            "title": 'Text, with a "quote"\r\nand another line',
            "score": -10,
        },
        {
            "=header": "  +second",
            "title": "\tplain",
            "context": "@third",
            "company": "\ufeff－fourth",
        },
    ]

    json_file, csv_file = export_leads(leads, str(tmp_path / "leads"))

    with open(csv_file, newline="", encoding="utf-8") as file:
        assert list(csv.reader(file)) == [
            ["'=header", "title", "score", "context", "company"],
            ["'=first", leads[0]["title"], "-10", "", ""],
            ["'  +second", "'\tplain", "", "'@third", "'\ufeff－fourth"],
        ]
    with open(json_file, encoding="utf-8") as file:
        assert json.load(file) == leads


def test_converter_neutralizes_outreach_fields(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fixture = tmp_path / "gig3_3d_leads_20260420_012832.json"
    fixture.write_text(
        json.dumps([{"author": "=author", "title": "  -title", "outreach_message": "+draft"}]),
        encoding="utf-8",
    )

    runpy.run_module("convert_leads", run_name="__main__")

    with (tmp_path / "GIG3_FULL_LEAD_LIST.csv").open(newline="", encoding="utf-8") as file:
        [row] = csv.DictReader(file)
    assert row["Lead Name"] == "'=author"
    assert row["Project Title"] == "'  -title"
    assert row["Outreach Message"] == "'+draft"


def test_standalone_github_export_neutralizes_profile_fields(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    search = "https://api.github.com/search/users?q=AI+Agency+type:user&per_page=30&page=1"
    profile = "https://api.github.com/users/fixture"
    responses = {
        search: {
            "items": [{"login": "fixture", "html_url": "https://example.invalid", "url": profile}]
        },
        profile: {"email": "fixture@example.invalid", "company": "@company", "blog": "\t+site"},
    }
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request: io.BytesIO(json.dumps(responses[request.full_url]).encode()),
    )
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    runpy.run_module("github_lead_scraper", run_name="__main__")

    with (tmp_path / "premium_b2b_leads.csv").open(newline="", encoding="utf-8") as file:
        [row] = csv.DictReader(file)
    assert row["Company"] == "'@company"
    assert row["Website/Blog"] == "'\t+site"
