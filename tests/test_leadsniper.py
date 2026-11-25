"""Smoke and regression tests for LeadSniper modules."""
import importlib
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_github_lead_scraper_imports_and_headers():
    mod = importlib.import_module("github_lead_scraper")
    assert hasattr(mod, "os")
    assert callable(mod.scrape_github_leads)
    assert callable(mod.get_email_from_events)


def test_fresh_gig_scanner_keywords():
    mod = importlib.import_module("fresh_gig_scanner")
    assert "python" in mod.SKILL_KEYWORDS
    assert len(mod.SUBREDDITS_AND_QUERIES) >= 5
