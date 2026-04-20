#!/usr/bin/env python3
"""
FRESH GIG SCANNER v2 — Continuous Reddit scraper for new gig opportunities.
Searches multiple subreddits for tasks posted in the last 24 hours.
Runs while you eat. Results saved to fresh_gigs_<timestamp>.json
"""
import json, time, urllib.request, urllib.parse
from datetime import datetime, timezone

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

SUBREDDITS_AND_QUERIES = [
    # High-conversion gig boards
    ("slavelabour", "task", 25),
    ("slavelabour", "offer", 15),
    ("forhire", "hiring", 25),
    ("forhire", "for hire", 15),
    # Niche skill boards  
    ("hiring", "remote", 15),
    ("freelance", "looking for", 10),
    ("digitalnomad", "hiring", 10),
    # Tech-specific
    ("webdev", "hiring", 10),
    ("learnprogramming", "need help", 10),
]

SKILL_KEYWORDS = [
    "video edit", "editing", "editor",
    "python", "script", "automat", "bot",
    "lead gen", "outreach", "scraping", "scraper",
    "social media", "content", "posting",
    "ai", "chatgpt", "gpt", "llm",
    "web", "website", "landing page",
    "data entry", "virtual assistant",
    "email", "cold email",
    "design", "canva", "graphic",
    "youtube", "shorts", "tiktok",
]

def fetch_subreddit(subreddit, query, limit):
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={encoded}&sort=new&limit={limit}&restrict_sr=on&t=day"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            posts = []
            for child in data.get("data", {}).get("children", []):
                d = child["data"]
                posts.append({
                    "title": d.get("title", ""),
                    "author": d.get("author", ""),
                    "subreddit": subreddit,
                    "url": f"https://reddit.com{d.get('permalink', '')}",
                    "body": d.get("selftext", "")[:500],
                    "score": d.get("score", 0),
                    "num_comments": d.get("num_comments", 0),
                    "created_utc": d.get("created_utc", 0),
                    "created_readable": datetime.fromtimestamp(
                        d.get("created_utc", 0), tz=timezone.utc
                    ).strftime("%Y-%m-%d %H:%M UTC"),
                })
            return posts
    except Exception as e:
        print(f"    [!] Error on r/{subreddit}: {e}")
        return []

def score_relevance(post):
    """Score how relevant a post is to our skills. Higher = better match."""
    text = (post["title"] + " " + post["body"]).lower()
    score = 0
    matched = []
    for kw in SKILL_KEYWORDS:
        if kw in text:
            score += 1
            matched.append(kw)
    # Bonus for task/hiring flair
    title_lower = post["title"].lower()
    if "[task]" in title_lower or "[hiring]" in title_lower:
        score += 3
    if any(x in title_lower for x in ["$", "usd", "budget", "pay", "paid"]):
        score += 2
    post["relevance_score"] = score
    post["matched_keywords"] = matched
    return score

def main():
    print("=" * 60)
    print("  FRESH GIG SCANNER v2 - Hunting new opportunities...")
    print("=" * 60)
    
    all_posts = []
    for sub, query, limit in SUBREDDITS_AND_QUERIES:
        print(f"  [*] r/{sub} -> '{query}' (limit {limit})")
        posts = fetch_subreddit(sub, query, limit)
        print(f"      Got {len(posts)} posts")
        all_posts.extend(posts)
        time.sleep(2)
    
    # Dedup by URL
    seen_urls = set()
    unique = []
    for p in all_posts:
        if p["url"] not in seen_urls and p["author"] != "[deleted]":
            seen_urls.add(p["url"])
            unique.append(p)
    
    # Score and sort
    for p in unique:
        score_relevance(p)
    unique.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    # Export
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = f"fresh_gigs_{ts}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    
    # Also export top hits as simple text for quick copy
    top_file = f"TOP_GIGS_{ts}.txt"
    with open(top_file, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"  TOP GIGS FOUND - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 60 + "\n\n")
        for i, p in enumerate(unique[:20], 1):
            f.write(f"#{i} [Score: {p['relevance_score']}] {p['title']}\n")
            f.write(f"   Author: u/{p['author']} | r/{p['subreddit']}\n")
            f.write(f"   URL: {p['url']}\n")
            f.write(f"   Keywords: {', '.join(p['matched_keywords'])}\n")
            f.write(f"   Posted: {p['created_readable']}\n")
            if p['body']:
                f.write(f"   Preview: {p['body'][:200].replace(chr(10), ' ')}\n")
            f.write("\n")
    
    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {len(unique)} unique gigs found")
    print(f"  Top scored: {len([p for p in unique if p['relevance_score'] >= 3])} high-match gigs")
    print(f"  Exported: {outfile}")
    print(f"  Top list: {top_file}")
    print(f"{'=' * 60}")
    
    # Print top 10
    print("\n  --- TOP 10 MATCHES ---")
    for i, p in enumerate(unique[:10], 1):
        print(f"  {i}. [Score {p['relevance_score']}] {p['title'][:70]}")
        print(f"     u/{p['author']} | r/{p['subreddit']} | {p['url']}")
        if p['matched_keywords']:
            print(f"     Keywords: {', '.join(p['matched_keywords'])}")
        print()

if __name__ == "__main__":
    main()
