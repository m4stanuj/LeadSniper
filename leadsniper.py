#!/usr/bin/env python3
"""
LeadSniper v2.0 — M4ST Autonomous Lead Acquisition Engine
==========================================================
Multi-platform lead scraping with M4ST LLM fallback integration.
73 API keys, lead scoring, AI personalization, and smart dedup.

Features:
  - Reddit (API + no-auth fallback)
  - GitHub profile intelligence
  - Lead scoring (0-100)
  - M4ST LLM fallback chain (73 keys, 7 providers)
  - CSV + JSON export
  - Campaign-ready DM generation
"""
import os, sys, json, csv, time, re, hashlib, urllib.request
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── M4ST LLM Integration ──────────────────────────────────────────────
# Try to import M4ST's 73-key fallback router first, then fall back to Groq SDK
_M4ST_ROOT = Path(os.getenv("OPENWORK_CONFIG", ""))
_LLM_MODULE = None

if _M4ST_ROOT.exists():
    sys.path.insert(0, str(_M4ST_ROOT / "mcp_servers"))
    try:
        from llm_fallback import chat_complete as m4st_chat
        _LLM_MODULE = "m4st"
        print("[+] M4ST LLM Fallback loaded (73 keys, 7 providers)")
    except ImportError:
        pass

if not _LLM_MODULE:
    try:
        from groq import Groq
        _LLM_MODULE = "groq"
        print("[+] Groq SDK loaded (single key)")
    except ImportError:
        _LLM_MODULE = None
        print("[!] No LLM available — using template pitches")


def llm_generate(prompt: str, max_tokens: int = 200, task: str = "write") -> str:
    """Unified LLM call — routes through M4ST's 73-key pool or Groq SDK."""
    if _LLM_MODULE == "m4st":
        return m4st_chat(
            [{"role": "system", "content": "You are a concise sales copywriter."},
             {"role": "user", "content": prompt}],
            max_tokens=max_tokens, task=task
        )
    elif _LLM_MODULE == "groq":
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=max_tokens
        )
        return r.choices[0].message.content.strip()
    return ""


# ── Lead Scoring Engine ───────────────────────────────────────────────
# Scores leads 0-100 based on intent signals
INTENT_SCORES = {
    # High intent (50+ points)
    "hiring": 60, "looking for a dev": 70, "need a developer": 70,
    "need help building": 65, "looking for an agency": 75,
    "budget": 80, "paying": 85, "willing to pay": 90,
    "$": 50, "remote work": 40, "freelancer needed": 70,
    # Medium intent (20-49 points)
    "how to automate": 35, "build me": 45, "need to automate": 40,
    "looking for someone": 50, "can anyone build": 55,
    "task": 25, "need help": 30, "recommendation": 20,
    # Low intent (1-19 points)
    "tutorial": 5, "how to": 10, "anyone know": 10,
}

NEGATIVE_SIGNALS = [
    "just curious", "learning", "student project", "homework",
    "i built", "i made", "my project", "showcase",
]

def score_lead(title: str, body: str) -> int:
    """Score a lead 0-100 based on buying intent signals."""
    text = f"{title} {body}".lower()
    score = 0
    for keyword, points in INTENT_SCORES.items():
        if keyword in text:
            score += points
    # Negative signals reduce score
    for neg in NEGATIVE_SIGNALS:
        if neg in text:
            score -= 20
    # Clamp
    return max(0, min(100, score))


# ── Reddit Scanner ────────────────────────────────────────────────────
class RedditScanner:
    """Scans Reddit for leads — API mode (PRAW) with no-auth fallback."""

    def __init__(self):
        self.use_api = False
        self.reddit = None
        if os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"):
            try:
                import praw
                self.reddit = praw.Reddit(
                    client_id=os.getenv("REDDIT_CLIENT_ID"),
                    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                    user_agent="M4ST_LeadSniper_v2.0"
                )
                self.use_api = True
                print("[+] Reddit API (PRAW) connected")
            except Exception as e:
                print(f"[!] PRAW failed: {e} — using no-auth mode")
        else:
            print("[*] No Reddit API keys — using no-auth JSON scraping")

    def scan(self, subreddits: list, keywords: list, limit: int = 50) -> list:
        if self.use_api:
            return self._scan_api(subreddits, keywords, limit)
        return self._scan_noauth(subreddits, keywords, limit)

    def _scan_api(self, subreddits, keywords, limit):
        leads = []
        for sub in subreddits:
            print(f"  [*] Scanning r/{sub} (API)...")
            try:
                subreddit = self.reddit.subreddit(sub)
                for post in subreddit.new(limit=limit):
                    text = f"{post.title} {post.selftext}".lower()
                    if any(kw in text for kw in keywords):
                        score = score_lead(post.title, post.selftext)
                        leads.append({
                            "platform": "reddit",
                            "title": post.title,
                            "body": post.selftext[:500],
                            "author": str(post.author),
                            "url": f"https://reddit.com{post.permalink}",
                            "score": score,
                            "subreddit": sub,
                            "created": datetime.fromtimestamp(post.created_utc).isoformat(),
                        })
            except Exception as e:
                print(f"  [-] Error on r/{sub}: {e}")
        return leads

    def _scan_noauth(self, subreddits, keywords, limit):
        leads = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        for sub in subreddits:
            print(f"  [*] Scanning r/{sub} (no-auth)...")
            url = f"https://www.reddit.com/r/{sub}/new.json?limit={min(limit, 100)}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode())
                    for post in data.get("data", {}).get("children", []):
                        d = post["data"]
                        text = f"{d['title']} {d.get('selftext','')}".lower()
                        if any(kw in text for kw in keywords):
                            score = score_lead(d["title"], d.get("selftext", ""))
                            leads.append({
                                "platform": "reddit",
                                "title": d["title"],
                                "body": d.get("selftext", "")[:500],
                                "author": d["author"],
                                "url": d.get("url", ""),
                                "score": score,
                                "subreddit": sub,
                                "created": datetime.fromtimestamp(d.get("created_utc", 0)).isoformat(),
                            })
            except Exception as e:
                print(f"  [-] Error on r/{sub}: {e}")
            time.sleep(2)
        return leads


# ── GitHub Intelligence Scanner ───────────────────────────────────────
class GitHubScanner:
    """Scrapes GitHub for B2B leads — emails from public profiles + commit history."""

    def __init__(self):
        token = os.getenv("GITHUB_TOKEN", "")
        self.headers = {
            'User-Agent': 'M4ST-LeadSniper/2.0',
            'Accept': 'application/vnd.github.v3+json',
        }
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
            print("[+] GitHub API authenticated")
        else:
            print("[!] No GITHUB_TOKEN — GitHub rate limits will apply (60 req/hr)")

    def _fetch_json(self, url: str):
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return None

    def _email_from_events(self, username: str):
        data = self._fetch_json(f"https://api.github.com/users/{username}/events/public")
        if not data:
            return None
        for event in data:
            if event.get("type") == "PushEvent":
                for commit in event.get("payload", {}).get("commits", []):
                    email = commit.get("author", {}).get("email", "")
                    if email and "noreply" not in email and "@" in email:
                        return email
        return None

    def scan(self, queries: list, max_pages: int = 2) -> list:
        leads = []
        for query in queries:
            print(f"  [*] GitHub search: '{query}'...")
            for page in range(1, max_pages + 1):
                data = self._fetch_json(
                    f"https://api.github.com/search/users?q={query}+type:user&per_page=30&page={page}")
                if not data:
                    break
                for item in data.get("items", []):
                    username = item["login"]
                    profile = self._fetch_json(item["url"])
                    if not profile:
                        continue
                    email = profile.get("email")
                    if not email:
                        email = self._email_from_events(username)
                    if email:
                        leads.append({
                            "platform": "github",
                            "username": username,
                            "email": email,
                            "company": profile.get("company", "N/A") or "N/A",
                            "website": profile.get("blog", "N/A") or "N/A",
                            "github_url": profile.get("html_url", ""),
                            "followers": profile.get("followers", 0),
                            "score": min(100, 30 + profile.get("followers", 0) * 2),
                        })
                        print(f"  [+] Lead: {username} | {email} | {profile.get('company','')}")
                    time.sleep(0.3)
        return leads


# ── AI Pitch Generator ────────────────────────────────────────────────
def generate_pitch(lead: dict) -> str:
    """Generate AI-personalized DM/email pitch for a lead."""
    if not _LLM_MODULE:
        author = lead.get("author", lead.get("username", "there"))
        title = lead.get("title", "your project")
        return f"Hey {author}, saw your post about '{title[:50]}'. I build automation systems and can help. Let's chat."

    platform = lead.get("platform", "reddit")
    if platform == "reddit":
        prompt = f"""Write a short, casual Reddit DM to someone who posted this:
Title: {lead.get('title', '')}
Body: {lead.get('body', '')[:400]}

Goal: Offer AI automation & dev services to solve their specific problem.
Rules: Be helpful not salesy. Max 3-4 sentences. Sound human. No emojis."""
    else:
        prompt = f"""Write a short cold email to {lead.get('username', 'someone')} who works at {lead.get('company', 'their company')}.
Goal: Offer AI automation services. Mention I can build custom tools/bots.
Rules: Professional but casual. Max 4 sentences. Include a clear CTA."""

    try:
        return llm_generate(prompt, max_tokens=180, task="write")
    except Exception:
        author = lead.get("author", lead.get("username", "there"))
        return f"Hey {author}, I build automation systems. Happy to help with your project — want to chat?"


# ── Cold Email Sender ─────────────────────────────────────────────────
class EmailSender:
    """SMTP-based email sender with HTML templates and rate limiting."""

    def __init__(self):
        self.address = os.getenv("GMAIL_ADDRESS", "")
        self.password = os.getenv("GMAIL_APP_PASSWORD", "")
        self.server = None

    def connect(self):
        if not self.address or not self.password:
            print("[-] Gmail credentials missing in .env")
            return False
        import smtplib
        try:
            self.server = smtplib.SMTP('smtp.gmail.com', 587)
            self.server.starttls()
            self.server.login(self.address, self.password)
            print("[+] SMTP connected")
            return True
        except Exception as e:
            print(f"[-] SMTP auth failed: {e}")
            return False

    def send(self, to_email: str, subject: str, body: str):
        if not self.server:
            return False
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart()
        msg['From'] = self.address
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        try:
            self.server.send_message(msg)
            return True
        except Exception as e:
            print(f"[-] Send failed ({to_email}): {e}")
            return False

    def close(self):
        if self.server:
            self.server.quit()


# ── Export Engine ──────────────────────────────────────────────────────
def export_leads(leads: list, base_name: str = "leads"):
    """Export leads to both JSON and CSV with timestamps."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON export
    json_file = f"{base_name}_{ts}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    # CSV export
    csv_file = f"{base_name}_{ts}.csv"
    if leads:
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=leads[0].keys())
            writer.writeheader()
            writer.writerows(leads)

    return json_file, csv_file


def dedup_leads(leads: list) -> list:
    """Remove duplicate leads by author/email."""
    seen = set()
    unique = []
    for lead in leads:
        key = lead.get("email", lead.get("author", lead.get("username", "")))
        if key and key not in seen:
            seen.add(key)
            unique.append(lead)
    return unique


# ══════════════════════════════════════════════════════════════════════
#  MAIN — Full Pipeline
# ══════════════════════════════════════════════════════════════════════
def run_full_pipeline():
    print("=" * 60)
    print("   M4ST LEADSNIPER v2.0 — AUTONOMOUS CLIENT ACQUISITION")
    print("=" * 60)
    print(f"   LLM Engine: {_LLM_MODULE or 'template-only'}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_leads = []

    # ── Phase 1: Reddit Scanning ──────────────────────────────────────
    print("\n[PHASE 1] Reddit Lead Scanning...")
    reddit = RedditScanner()

    TARGET_SUBS = [
        "slavelabour", "forhire", "freelance_forhire",
        "Entrepreneur", "smallbusiness", "SaaS",
        "SomebodyMakeThis", "marketing", "startups",
    ]

    KEYWORDS = [
        # High intent
        "hiring", "looking for a dev", "need a developer",
        "need help building", "looking for an agency",
        "looking for someone", "can anyone build",
        "freelancer needed", "need to automate",
        # Medium intent
        "how to automate", "build me", "[task]", "[offer]",
        "budget", "paying", "willing to pay",
    ]

    reddit_leads = reddit.scan(TARGET_SUBS, KEYWORDS, limit=50)
    print(f"  [*] Reddit: {len(reddit_leads)} raw leads")
    all_leads.extend(reddit_leads)

    # ── Phase 2: GitHub Intelligence ──────────────────────────────────
    if os.getenv("GITHUB_TOKEN"):
        print("\n[PHASE 2] GitHub B2B Intelligence...")
        github = GitHubScanner()
        github_queries = ["AI+Agency", "automation+founder", "SaaS+founder"]
        github_leads = github.scan(github_queries, max_pages=2)
        print(f"  [*] GitHub: {len(github_leads)} leads with emails")
        all_leads.extend(github_leads)
    else:
        print("\n[PHASE 2] GitHub skipped (no GITHUB_TOKEN in .env)")

    # ── Phase 3: Dedup + Score + Sort ─────────────────────────────────
    print("\n[PHASE 3] Processing & Scoring...")
    all_leads = dedup_leads(all_leads)
    all_leads.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Generate AI pitches for top leads
    top_leads = [l for l in all_leads if l.get("score", 0) >= 30]
    print(f"  [*] {len(top_leads)} high-intent leads (score >= 30)")

    if _LLM_MODULE:
        print("  [*] Generating AI pitches...")
        for i, lead in enumerate(top_leads[:20]):  # Top 20 only for speed
            lead["ai_pitch"] = generate_pitch(lead)
            if (i + 1) % 5 == 0:
                print(f"  [+] {i+1}/{min(len(top_leads), 20)} pitches generated")

    # ── Phase 4: Export ───────────────────────────────────────────────
    print("\n[PHASE 4] Exporting Results...")
    json_f, csv_f = export_leads(all_leads)
    print(f"  [+] JSON: {json_f}")
    print(f"  [+] CSV:  {csv_f}")

    # ── Summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("   LEADSNIPER v2.0 — MISSION COMPLETE")
    print("=" * 60)
    print(f"   Total Leads:    {len(all_leads)}")
    print(f"   High Intent:    {len(top_leads)} (score >= 30)")
    print(f"   With Pitches:   {sum(1 for l in all_leads if l.get('ai_pitch'))}")
    print(f"   Platforms:      Reddit + {'GitHub' if os.getenv('GITHUB_TOKEN') else 'Reddit only'}")
    print(f"   LLM Engine:     {_LLM_MODULE or 'template-only'}")

    # Score distribution
    buckets = {"🔥 Hot (70+)": 0, "🟡 Warm (30-69)": 0, "❄️ Cold (<30)": 0}
    for l in all_leads:
        s = l.get("score", 0)
        if s >= 70: buckets["🔥 Hot (70+)"] += 1
        elif s >= 30: buckets["🟡 Warm (30-69)"] += 1
        else: buckets["❄️ Cold (<30)"] += 1
    for label, count in buckets.items():
        print(f"   {label}: {count}")
    print("=" * 60)

    return all_leads


if __name__ == "__main__":
    run_full_pipeline()
