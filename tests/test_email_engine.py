import json
import runpy
import smtplib
import socket
import sys
from unittest.mock import Mock

import pytest

from cold_email_engine import ColdEmailEngine
from leadsniper import EmailSender


@pytest.fixture
def prevent_network(monkeypatch):
    monkeypatch.setenv("GMAIL_ADDRESS", "sender@example.invalid")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "fixture")
    monkeypatch.setenv("GROQ_API_KEY", "fixture")
    failure = AssertionError("drafts must not open a connection")
    connection = Mock(side_effect=failure)
    smtp = Mock(side_effect=failure)
    monkeypatch.setattr(socket, "create_connection", connection)
    monkeypatch.setattr(smtplib, "SMTP", smtp)
    yield
    connection.assert_not_called()
    smtp.assert_not_called()


def test_default_command_writes_only_a_local_report(tmp_path, monkeypatch, prevent_network):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["cold_email_engine.py"])
    (tmp_path / "premium_b2b_leads.csv").write_text(
        "Username,Email,Company\n"
        "Alice,alice@example.invalid,Example\n"
        "Bob,no-reply@example.invalid,Example\n"
        "Carol,carol@example.invalid,Example\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as status:
        runpy.run_module("cold_email_engine", run_name="__main__")

    assert status.value.code == 0
    (report_path,) = tmp_path.glob("campaign_drafts_*.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["mode"] == "draft"
    assert report["input_rows"] == 3
    assert report["sent_count"] == 0
    assert [draft["email"] for draft in report["drafts"]] == [
        "alice@example.invalid",
        "carol@example.invalid",
    ]
    assert report["drafts"][0]["subject"].endswith("at Example")
    assert report["drafts"][0]["body"].startswith("Hi Alice,")


def test_default_campaign_api_writes_limited_report(tmp_path, monkeypatch, prevent_network):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "input.csv"
    source.write_text(
        "username,email\n"
        "Ada,ada@example.invalid\n"
        "Grace,grace@example.invalid\n"
        "Bot,noreply@example.invalid\n",
        encoding="utf-8-sig",
    )

    report_path = ColdEmailEngine().fire_campaign(source, max_emails=1)

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["eligible_rows"] == 2
    assert report["draft_count"] == 1
    assert report["drafts"][0]["email"] == "ada@example.invalid"


def test_default_smtp_helpers_never_use_the_transport(prevent_network):
    campaign = ColdEmailEngine()
    sender = EmailSender()
    transport = Mock()
    campaign.server = sender.server = transport

    assert not campaign.connect()
    assert not sender.connect()
    assert not campaign.send_email("recipient@example.invalid", "Subject", "Body")
    assert not sender.send("recipient@example.invalid", "Subject", "Body")
    transport.send_message.assert_not_called()


def test_draft_review_report_explains_exclusions_and_keeps_first_duplicate(tmp_path, prevent_network):
    source = tmp_path / "input.csv"
    source.write_text(
        "Username,Email,Company\n"
        "Ada,ada@example.invalid,First\n"
        "Duplicate,ADA@example.invalid,Second\n"
        "Grace,grace@example.invalid,Third\n"
        "Nobody,invalid,Fourth\n",
        encoding="utf-8",
    )
    report_path = ColdEmailEngine().draft_campaign(source, max_drafts=1, output=tmp_path / "review.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["input_rows"] == 4
    assert report["invalid_or_excluded_rows"] == 1
    assert report["duplicate_rows"] == 1
    assert report["unique_recipients"] == 2
    assert report["omitted_by_limit"] == 1
    assert report["sent_count"] == 0
    assert len(report["drafts"]) == 1
    assert report["drafts"][0]["email"] == "ada@example.invalid"
    assert report["drafts"][0]["subject"].endswith("at First")
    assert report["drafts"][0]["review_status"] == "pending"
