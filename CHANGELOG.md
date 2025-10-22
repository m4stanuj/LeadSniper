# Changelog

All notable changes to LeadSniper are documented here.

## [2.3.0] — 2026-04-18

### Added
- `leadsniper_fast.py` — lightweight scanner for quick target sweeps
- `revenue_blitz.py` — automated multi-platform lead funnel
- `convert_leads.py` — batch lead-to-pitch converter with LLM routing
- Deliverable template system (`gig3_deliverable_sample.json`)

### Fixed
- Reddit JSON scraping fallback when PRAW auth expires
- Email threading for follow-up sequences

## [2.2.0] — 2026-03-05

### Added
- Multi-LLM pitch generation with M4STCLAW fallback chain
- Intent scoring algorithm v2 (weighted keyword + context analysis)
- CSV export for CRM integration

### Changed
- Switched from requests to httpx for async HTTP operations

## [2.1.0] — 2026-01-15

### Added
- Reddit no-auth JSON scraping as PRAW fallback
- Subreddit intent heatmap generation
- Proxy rotation pool support

## [2.0.0] — 2025-10-22

### Added
- **Complete rewrite** from prototype to production architecture
- PRAW-based Reddit scraping with multi-subreddit targeting
- SMTP email integration with Gmail app passwords
- LLM-powered personalized pitch generation
- Rate-limit aware scheduling

### Breaking Changes
- New `.env` format required — see `.env.example`

## [1.0.0] — 2025-05-10

### Added
- Initial prototype — manual lead scraping + basic email outreach
- Single subreddit support
- Template-based pitch generation
