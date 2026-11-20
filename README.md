# LeadSniper

[![CI Pipeline](https://github.com/m4stanuj/LeadSniper/actions/workflows/ci.yml/badge.svg)](https://github.com/m4stanuj/LeadSniper/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Workflow: Review First](https://img.shields.io/badge/workflow-review--first-00FF9D.svg)]()

LeadSniper is a B2B lead research workspace for collecting public signals, scoring prospects, reviewing context, and exporting clean lead batches.

Dashboard demo: open [`index.html`](index.html) for a static workspace with a sample lead queue, filters, workflow notes, and export preview.

## What It Does

- Collects lead candidates from public and authorized sources.
- Keeps source context attached to each lead.
- Scores prospects by fit, recency, and evidence strength.
- Supports review-first filtering before export.
- Exports reviewed batches for downstream outreach tools.
- Generates local email draft reports from a lead CSV for manual review.

## Architecture

```mermaid
graph LR
    A[Public Sources] --> B[Lead Collector]
    B --> C[Signal Normalizer]
    C --> D[Score + Reason]
    D --> E[Review Queue]
    E --> F[JSON / CSV Export]
```

## Installation

```bash
git clone https://github.com/m4stanuj/LeadSniper.git
cd LeadSniper

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -e .[dev]
```

## Local Demo

```bash
python -m http.server 8765
```

Then open:

```text
http://127.0.0.1:8765/index.html
```

## Local Outreach Drafts

```bash
python cold_email_engine.py premium_b2b_leads.csv --max-drafts 10
```

The installed package also exposes the same local draft workflow as `leadsniper-drafts`.

Each report starts drafts at `review_status: pending` and shows counts for excluded rows,
case-insensitive duplicate addresses, and unique recipients beyond the draft limit. The first
eligible row supplies the details for a duplicate address.

The command writes a timestamped `campaign_drafts_*.json` report with recipients, subjects,
message bodies, and counts. Each draft comes from a local template. The command
requires no email credentials or network connection. The input CSV needs an
`Email` or `email` column.

## Security Notes

- Keep API keys in `.env`; never commit secrets.
- Use public or explicitly authorized data sources only.
- Review lead context before exporting or using a list.
- Treat generated reports as contact data and review drafts before sharing.
- CSV exports mark formula-like cell values as text. Use JSON when you need the original values.

## Example Batch Metrics

| Metric | Value |
|---|---:|
| Prospects collected | 184 |
| Qualified leads | 37 |
| Needs review | 12 |
| Exported automatically | 0 |

## Tests

```bash
pytest tests -q
```

## License

MIT. See [LICENSE](LICENSE).

