#!/usr/bin/env python3
"""
cold_email_engine.py — M4ST AI Cold Outreach Engine v2.0
=========================================================
Sends personalized cold emails using AI-generated pitches.
Supports M4ST LLM fallback (73 keys) or Groq SDK.

Features:
  - AI-generated subject lines & body copy
  - HTML email templates (professional look)
  - Rate limiting (configurable delay)
  - Send tracking & reporting
  - CSV lead ingestion
"""
import csv, smtplib, time, os, sys, json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── M4ST LLM Integration ──────────────────────────────────────────────
_M4ST_ROOT = Path(os.getenv("OPENWORK_CONFIG", ""))
_LLM_MODULE = None

if _M4ST_ROOT.exists():
    sys.path.insert(0, str(_M4ST_ROOT / "mcp_servers"))
    try:
        from llm_fallback import chat_complete as m4st_chat
        _LLM_MODULE = "m4st"
    except ImportError:
        pass

if not _LLM_MODULE:
    try:
        from groq import Groq
        _LLM_MODULE = "groq"
    except ImportError:
        _LLM_MODULE = None


def ai_generate(prompt: str, max_tokens: int = 250) -> str:
    """Generate text using M4ST's 73-key pool or Groq SDK."""
    if _LLM_MODULE == "m4st":
        return m4st_chat(
            [{"role": "system", "content": "You are an expert B2B cold email copywriter. Write concise, high-converting emails."},
             {"role": "user", "content": prompt}],
            max_tokens=max_tokens, task="write"
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


class ColdEmailEngine:
    def __init__(self):
        print("=" * 60)
        print("   M4ST COLD OUTREACH ENGINE v2.0")
        print("=" * 60)
        print(f"   LLM: {_LLM_MODULE or 'template-only'}")

        self.email_address = os.getenv("GMAIL_ADDRESS", "")
        self.app_password = os.getenv("GMAIL_APP_PASSWORD", "")
        self.server = None
        self.sent_count = 0
        self.fail_count = 0
        self.log = []

        if not self.email_address or not self.app_password:
            print("[-] CRITICAL: GMAIL_ADDRESS or GMAIL_APP_PASSWORD missing in .env")
            print("[-] Get App Password: https://myaccount.google.com/apppasswords")
            return

    def connect(self) -> bool:
        """Connect to Gmail SMTP with TLS."""
        try:
            self.server = smtplib.SMTP('smtp.gmail.com', 587)
            self.server.starttls()
            self.server.login(self.email_address, self.app_password)
            print("[+] SMTP authenticated successfully")
            return True
        except Exception as e:
            print(f"[-] SMTP auth failed: {e}")
            return False

    def generate_pitch(self, lead: dict) -> tuple:
        """Generate personalized subject + body for a lead."""
        username = lead.get("Username", lead.get("username", "there"))
        company = lead.get("Company", lead.get("company", ""))
        email = lead.get("Email", lead.get("email", ""))
        website = lead.get("Website/Blog", lead.get("website", ""))

        # AI-generated pitch
        if _LLM_MODULE:
            prompt = f"""Write a cold email for B2B outreach.

Target: {username}
Company: {company or 'Unknown'}
Website: {website or 'N/A'}

I offer AI automation services — custom bots, lead gen tools, workflow automation.
Write ONLY the email body (no subject line). Max 5 sentences.
Be specific about how I can help THEIR business.
Include a clear CTA (call to action). Sound casual and human."""

            body = ai_generate(prompt, max_tokens=200)
            if body:
                # Generate subject line separately
                subj_prompt = f"Write a 5-8 word cold email subject line for {username} at {company or 'a tech company'}. About AI automation services. Just the subject, nothing else."
                subject = ai_generate(subj_prompt, max_tokens=20)
                if subject:
                    subject = subject.strip('"').strip("'").strip()
                else:
                    subject = f"Quick idea for {company or 'your team'}"
                return subject, body

        # Template fallback
        company_part = f" at {company}" if company and company != "N/A" else ""
        subject = f"Quick question about automation{company_part}"
        body = f"""Hi {username},

I'm a developer who builds custom AI automation tools. I recently built a system that automatically finds and qualifies leads using AI — saving teams 10+ hours/week.

Since you're active in the space{company_part}, I thought this might be relevant for you.

Would you be open to a quick 5-min chat about how automation could help your workflow?

Best,
Anuj (M4ST Autonomous Systems)"""
        return subject, body

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send a single email with tracking."""
        if not self.server:
            return False

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Anuj | M4ST <{self.email_address}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        # Plain text version
        msg.attach(MIMEText(body, 'plain'))

        # HTML version (cleaner inbox rendering)
        html_body = f"""<html><body style="font-family: -apple-system, Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.6;">
{body.replace(chr(10), '<br>')}
<br><br>
<span style="color: #888; font-size: 12px;">—<br>Sent via M4ST Autonomous Systems</span>
</body></html>"""
        msg.attach(MIMEText(html_body, 'html'))

        try:
            self.server.send_message(msg)
            self.sent_count += 1
            self.log.append({"email": to_email, "subject": subject, "status": "sent", "time": datetime.now().isoformat()})
            return True
        except Exception as e:
            self.fail_count += 1
            self.log.append({"email": to_email, "subject": subject, "status": f"failed: {e}", "time": datetime.now().isoformat()})
            return False

    def fire_campaign(self, csv_filepath: str, delay: int = 5, max_emails: int = 50):
        """Execute email campaign from CSV file."""
        print(f"\n[*] Loading leads from {csv_filepath}...")
        try:
            with open(csv_filepath, 'r', encoding='utf-8') as f:
                leads = list(csv.DictReader(f))
        except Exception as e:
            print(f"[-] Error reading CSV: {e}")
            return

        # Filter leads with valid emails
        valid = [l for l in leads if l.get('Email') and
                 '@' in l.get('Email', '') and
                 'noreply' not in l.get('Email', '').lower() and
                 l.get('Email') != 'Requires Manual Check']

        print(f"[*] {len(valid)} valid targets out of {len(leads)} total")
        print(f"[*] Delay: {delay}s between emails | Max: {max_emails}")

        if not self.connect():
            return

        for i, lead in enumerate(valid[:max_emails]):
            target = lead['Email']
            subject, body = self.generate_pitch(lead)

            if self.send_email(target, subject, body):
                print(f"  [+] SENT ({i+1}/{min(len(valid), max_emails)}): {target}")
            else:
                print(f"  [-] FAIL ({i+1}): {target}")

            time.sleep(delay)

        self.close()
        self._print_report()

    def _print_report(self):
        """Print campaign summary."""
        print("\n" + "=" * 60)
        print("   CAMPAIGN REPORT")
        print("=" * 60)
        print(f"   Sent:   {self.sent_count}")
        print(f"   Failed: {self.fail_count}")
        print(f"   Total:  {self.sent_count + self.fail_count}")
        rate = (self.sent_count / max(1, self.sent_count + self.fail_count)) * 100
        print(f"   Success Rate: {rate:.1f}%")
        print("=" * 60)

        # Save log
        log_file = f"campaign_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(self.log, f, indent=2)
        print(f"   Log saved: {log_file}")

    def close(self):
        if self.server:
            try:
                self.server.quit()
            except Exception:
                pass


if __name__ == "__main__":
    engine = ColdEmailEngine()
    engine.fire_campaign("premium_b2b_leads.csv", delay=5, max_emails=50)
