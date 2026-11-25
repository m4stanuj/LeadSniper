import json
import os
import time
import urllib.error
import urllib.request


def get_email_from_events(username: str, headers: dict[str, str]) -> str | None:
    try:
        url = f"https://api.github.com/users/{username}/events/public"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            events = json.loads(resp.read().decode())
            for event in events:
                if event["type"] == "PushEvent":
                    for commit in event["payload"].get("commits", []):
                        email = commit["author"]["email"]
                        if email and "noreply" not in email:
                            return email
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError):
        return None
    return None


def scrape_github_leads(query: str, max_pages: int = 2) -> list[dict[str, str]]:
    print(f"[*] Extracting high-value leads for '{query}'...")
    leads: list[dict[str, str]] = []
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {
        "User-Agent": "M4ST-LeadSniper/2.0",
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        print("[+] GitHub API authenticated via GITHUB_TOKEN")
    else:
        print("[!] No GITHUB_TOKEN set — rate limit: 60 requests/hour")

    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/search/users?q={query}+type:user&per_page=30&page={page}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

                for item in data.get("items", []):
                    username = item["login"]
                    profile_url = item["html_url"]
                    user_req = urllib.request.Request(item["url"], headers=headers)
                    try:
                        with urllib.request.urlopen(user_req, timeout=10) as u_resp:
                            user_data = json.loads(u_resp.read().decode())
                            email = user_data.get("email")
                            company = user_data.get("company")
                            blog = user_data.get("blog")

                            if not email:
                                email = get_email_from_events(username, headers)

                            if email:
                                print(
                                    f"[+] Lead Acquired: {username} | {email} | {company or 'No Company'}"
                                )
                                leads.append(
                                    {
                                        "Username": username,
                                        "Email": email,
                                        "Company": company if company else "N/A",
                                        "Website/Blog": blog if blog else "N/A",
                                        "GitHub URL": profile_url,
                                    }
                                )
                    except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError):
                        continue
                    time.sleep(0.2)
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
            print(f"[-] Rate limit or network error on page {page}: {exc}. Stopping search.")
            break

    return leads


if __name__ == "__main__":
    print("=" * 60)
    print("   M4ST DATA BROKER - LEAD DISCOVERY RUNNER   ")
    print("=" * 60)
    all_leads = []
    for q in ["AI+Agency"]:
        all_leads.extend(scrape_github_leads(q, max_pages=1))
