import urllib.request
import json
import time

def scan_reddit_no_auth(subreddits, keywords, limit=25):
    leads = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for sub in subreddits:
        print(f"[*] Scanning r/{sub} without API keys...")
        url = f"https://www.reddit.com/r/{sub}/new.json?limit={limit}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                for post in data['data']['children']:
                    title = post['data']['title']
                    body = post['data'].get('selftext', '')
                    author = post['data']['author']
                    post_url = post['data']['url']
                    
                    text = f"{title} {body}".lower()
                    if any(kw in text for kw in keywords):
                        print(f"[+] LEAD FOUND: {title[:50]}... (u/{author})")
                        # Basic pitch template since we are skipping LLM for absolute speed
                        pitch = f"Hey {author}, saw your post about needing help. I run an automation/dev setup and can fix this for you right now. Let's lock it in."
                        
                        leads.append({
                            "title": title,
                            "author": author,
                            "url": post_url,
                            "suggested_dm": pitch
                        })
        except Exception as e:
            print(f"[-] Error scanning {sub}: {e}")
        time.sleep(2) # rate limit prevention
        
    return leads

if __name__ == "__main__":
    print("="*50)
    print("   M4ST LEAD SNIPER (FAST MODE - NO KEYS REQUIRED)   ")
    print("="*50)
    
    TARGET_SUBS = ["slavelabour", "forhire", "SomebodyMakeThis", "jobs", "freelance_forhire"]
    KEYWORDS = ["task", "hiring", "need a developer", "build me", "looking for", "automate"]
    
    leads = scan_reddit_no_auth(TARGET_SUBS, KEYWORDS, limit=30)
    
    with open("fast_leads.json", "w") as f:
        json.dump(leads, f, indent=4)
        
    print(f"\n[*] DONE! {len(leads)} raw leads extracted to fast_leads.json")
