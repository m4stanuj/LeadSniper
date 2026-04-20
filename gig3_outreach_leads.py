#!/usr/bin/env python3
"""
GIG #3 Lead Generator — 3D Visualization Client Outreach
=========================================================
Targeted lead scraping for u/BEEG_-BEEG_YOSHI's outreach task.
Finds businesses needing 3D visualization/rendering services.

Targets: Architects, Interior Designers, Real Estate Developers,
         Product Companies, Construction Firms

Platforms: Reddit, GitHub (for design tool companies)
"""
import json, time, urllib.request, urllib.parse
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def search_reddit(subreddit: str, query: str, limit: int = 25) -> list:
    """Search Reddit for leads needing 3D visualization."""
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={encoded_query}&sort=new&limit={limit}&restrict_sr=on"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            leads = []
            for post in data.get("data", {}).get("children", []):
                d = post["data"]
                leads.append({
                    "title": d["title"],
                    "author": d["author"],
                    "url": f"https://reddit.com{d['permalink']}",
                    "subreddit": subreddit,
                    "body_preview": d.get("selftext", "")[:300],
                    "created": datetime.fromtimestamp(d.get("created_utc", 0)).isoformat(),
                })
            return leads
    except Exception as e:
        print(f"  [-] Error: {e}")
        return []

def generate_outreach_message(lead: dict, service_type: str = "3D visualization") -> str:
    """Generate personalized outreach message for each lead."""
    author = lead.get("author", "there")
    title = lead.get("title", "your project")
    return f"""Hi {author},

I came across your post about "{title[:80]}" and thought our {service_type} services could be a great fit.

We specialize in:
• Photorealistic 3D renders for architecture & interiors
• Product visualization & packaging design
• Virtual staging for real estate listings
• Animated walkthroughs & fly-throughs

We've worked with architects, real estate developers, and product companies to bring their concepts to life with stunning, photorealistic visuals.

Would you be open to a quick chat about how we could help? I'd love to understand your specific needs and share some relevant portfolio pieces.

Best regards"""

def run_3d_lead_scraper():
    print("=" * 60)
    print("   GIG #3 — 3D VISUALIZATION LEAD SCRAPER")
    print("=" * 60)
    
    all_leads = []
    
    # Target subreddits and queries for 3D viz clients
    targets = [
        ("architecture", "need render"),
        ("architecture", "3D visualization"),
        ("architecture", "looking for renderer"),
        ("interiordesign", "need render"),
        ("interiordesign", "3D visualization"),
        ("realestateinvesting", "virtual staging"),
        ("realestate", "virtual staging"),
        ("Entrepreneur", "3D design"),
        ("smallbusiness", "product rendering"),
        ("graphic_design", "3D rendering"),
        ("forhire", "3D render"),
        ("forhire", "architectural visualization"),
    ]
    
    for subreddit, query in targets:
        print(f"  [*] Searching r/{subreddit} for '{query}'...")
        leads = search_reddit(subreddit, query, limit=10)
        print(f"      Found {len(leads)} results")
        all_leads.extend(leads)
        time.sleep(2)  # Rate limit
    
    # Dedup by author
    seen = set()
    unique_leads = []
    for lead in all_leads:
        if lead["author"] not in seen and lead["author"] != "[deleted]":
            seen.add(lead["author"])
            lead["outreach_message"] = generate_outreach_message(lead)
            unique_leads.append(lead)
    
    # Export
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"gig3_3d_leads_{ts}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_leads, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {len(unique_leads)} unique leads")
    print(f"  Exported: {output_file}")
    print(f"{'=' * 60}")
    
    # Show top 5
    print("\n  TOP LEADS:")
    for i, lead in enumerate(unique_leads[:10], 1):
        print(f"  {i}. u/{lead['author']} | r/{lead['subreddit']}")
        print(f"     {lead['title'][:80]}")
        print(f"     {lead['url']}")
        print()
    
    return unique_leads

if __name__ == "__main__":
    run_3d_lead_scraper()
