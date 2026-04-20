import urllib.request
import json
import csv
import time
import re

def get_email_from_events(username, headers):
    try:
        url = f"https://api.github.com/users/{username}/events/public"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            events = json.loads(resp.read().decode())
            for event in events:
                if event['type'] == 'PushEvent':
                    for commit in event['payload'].get('commits', []):
                        email = commit['author']['email']
                        if email and "noreply" not in email:
                            return email
    except Exception:
        pass
    return None

def scrape_github_leads(query, max_pages=2):
    print(f"[*] Extracting high-value leads for '{query}'...")
    leads = []
    # Load token from environment — NEVER hardcode PATs
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {
        'User-Agent': 'M4ST-LeadSniper/2.0',
        'Accept': 'application/vnd.github.v3+json',
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'
        print("[+] GitHub API authenticated via GITHUB_TOKEN")
    else:
        print("[!] No GITHUB_TOKEN set — rate limit: 60 requests/hour")
    
    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/search/users?q={query}+type:user&per_page=30&page={page}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
                for item in data.get('items', []):
                    username = item['login']
                    profile_url = item['html_url']
                    
                    # Fetch user profile
                    user_req = urllib.request.Request(item['url'], headers=headers)
                    try:
                        with urllib.request.urlopen(user_req) as u_resp:
                            user_data = json.loads(u_resp.read().decode())
                            email = user_data.get('email')
                            company = user_data.get('company')
                            blog = user_data.get('blog')
                            
                            # If no public email, dig into recent commits
                            if not email:
                                email = get_email_from_events(username, headers)
                                
                            if email:
                                print(f"[+] Lead Acquired: {username} | {email} | {company or 'No Company'}")
                                leads.append({
                                    "Username": username,
                                    "Email": email,
                                    "Company": company if company else "N/A",
                                    "Website/Blog": blog if blog else "N/A",
                                    "GitHub URL": profile_url
                                })
                    except Exception:
                        pass
                    time.sleep(0.2)
        except Exception as e:
            print(f"[-] Rate limit hit or error on page {page}. Stopping search.")
            break
            
    return leads

if __name__ == "__main__":
    print("="*60)
    print("   M4ST DATA BROKER - PREMIUM B2B LEAD EXTRACTOR   ")
    print("="*60)
    
    # Targeting high-income niches that buy software/services
    queries = ["AI+Agency"]
    
    all_leads = []
    for q in queries:
        all_leads.extend(scrape_github_leads(q, max_pages=1))
        
    # Deduplicate
    unique_leads = {lead["Username"]: lead for lead in all_leads}.values()
    
    csv_file = "premium_b2b_leads.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Username", "Email", "Company", "Website/Blog", "GitHub URL"])
        writer.writeheader()
        writer.writerows(unique_leads)
        
    print(f"\n[*] SUCCESS! {len(unique_leads)} Premium Leads saved to {csv_file}")
    print("[*] This CSV is ready to be sold for $50-$100 on BHW or Discord.")
