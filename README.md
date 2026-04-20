# LeadSniper v2.0 — AI-Powered Lead Generation & Outreach Engine

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
![AI](https://img.shields.io/badge/AI_Powered-LLM_Pipeline-purple?style=for-the-badge&logo=openai&logoColor=white)
![Status](https://img.shields.io/badge/Status-Production_Ready-green?style=for-the-badge)

**Autonomous lead generation system that scrapes, scores, and pitches — all powered by AI.**

[Features](#features) · [Architecture](#architecture) · [Quick Start](#quick-start) · [How It Works](#how-it-works)

</div>

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Platform Scraping** | Reddit, GitHub, LinkedIn-adjacent sources. Headless JSON + API fallback. |
| **AI Intent Scoring** | Ranks leads by buying intent using keyword matching + context analysis |
| **LLM Pitch Generation** | Auto-generates personalized cold emails/DMs using GPT/Groq/local LLMs |
| **73-Key API Rotation** | Zero-downtime LLM access via rotating API key pool with automatic failover |
| **Cold Email Engine** | SMTP-based outreach with HTML templates, rate limiting, and campaign tracking |
| **CSV/JSON Export** | Clean data pipeline — scrape to scored leads to outreach-ready exports |
| **Self-Healing Execution** | Automatic retry with exponential backoff on network failures |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LeadSniper v2.0                       │
├─────────────┬───────────────┬───────────────────────────┤
│   Scrapers  │   AI Engine   │     Outreach Pipeline     │
│             │               │                           │
│ ● Reddit    │ ● LLM Router  │ ● Cold Email Engine       │
│ ● GitHub    │ ● 73-Key Pool │ ● DM Template Generator   │
│ ● Web       │ ● Intent Score│ ● Campaign Tracker        │
│             │ ● Pitch Gen   │ ● Rate Limiter            │
└─────────────┴───────────────┴───────────────────────────┘
         │              │                    │
         ▼              ▼                    ▼
    Raw Leads → Scored & Ranked → Personalized Outreach
```

## Quick Start

```bash
# Clone
git clone https://github.com/yourusername/LeadSniper.git
cd LeadSniper

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your credentials

# Run — Scrape Reddit for hot leads
python leadsniper.py

# Run — Scrape targeted 3D/architecture leads
python gig3_outreach_leads.py

# Run — Scan for fresh freelance gigs
python fresh_gig_scanner.py

# Run — Fire cold email campaign
python cold_email_engine.py
```

## How It Works

### 1. Scrape
```python
# Multi-source lead extraction with rate limiting
leads = scrape_reddit(subreddits=["slavelabour", "forhire"], 
                      keywords=["hiring", "need developer"])
```

### 2. Score
```python
# AI-powered intent scoring
for lead in leads:
    lead.intent_score = score_buying_intent(lead.title, lead.body)
    # Factors: budget mentions, urgency words, skill match
```

### 3. Pitch
```python
# LLM generates personalized outreach
pitch = generate_pitch(lead, 
    service="AI automation",
    tone="casual professional")
```

### 4. Outreach
```python
# Automated email campaign with tracking
engine = ColdEmailEngine()
engine.fire_campaign("scored_leads.csv", delay=5)
```

## Project Structure

```
LeadSniper/
├── leadsniper.py           # Core Reddit lead scraper + AI scoring
├── fresh_gig_scanner.py    # Real-time gig opportunity scanner
├── gig3_outreach_leads.py  # Targeted niche lead scraper
├── cold_email_engine.py    # AI-powered cold email outreach
├── github_lead_scraper.py  # GitHub B2B lead extraction
├── portfolio.html          # Service showcase page
├── requirements.txt        # Dependencies
├── .env.example            # Configuration template
└── README.md               # You are here
```

## Tech Stack

- **Language:** Python 3.10+
- **AI/LLM:** OpenAI API, Groq SDK, custom LLM router with 73-key rotation
- **Scraping:** urllib, requests, BeautifulSoup (optional)
- **Email:** smtplib with TLS, MIME multipart HTML templates
- **Data:** JSON/CSV pipelines with deduplication

## Security

- All credentials stored in `.env` (never committed)
- API keys rotated automatically via fallback pool
- Rate limiting on all external requests
- No hardcoded secrets in codebase

## Results

In a single 2-hour session:
- **52 gigs** identified and scored across 9 subreddits
- **105 targeted leads** scraped for niche outreach
- **10 high-value opportunities** with ready-to-send pitches
- **$1000+** pipeline value generated

---

<div align="center">

**Built with AI. Delivered with precision.**

*Part of the M4STCLAW Autonomous Systems Architecture*

</div>
