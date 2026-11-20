#!/usr/bin/env python3
"""Generate local outreach drafts from a lead CSV for manual review."""

import argparse
import csv
import json
import os
import smtplib
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

def ai_generate(prompt: str, max_tokens: int = 250) -> str:
    """Generate text using M4ST's 73-key pool or Groq SDK."""
    llm_root = os.getenv("OPENWORK_CONFIG")
    if llm_root and Path(llm_root).is_dir():
        sys.path.insert(0, str(Path(llm_root) / "mcp_servers"))
        try:
            from llm_fallback import chat_complete as m4st_chat
        except ImportError:
            pass
        else:
            return m4st_chat(
                [
                    {"role": "system", "content": "Write concise B2B outreach drafts."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                task="write",
            )
        finally:
            sys.path.pop(0)

    if os.getenv("GROQ_API_KEY"):
        try:
            from groq import Groq
        except ImportError:
            return ""
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=max_tokens
        )
        return r.choices[0].message.content.strip()
    return ""


class ColdEmailEngine:
    def __init__(self, *, allow_send: bool = False):
        self._allow_send = allow_send is True
        if self._allow_send:
            from dotenv import load_dotenv

            load_dotenv()
        self.email_address = os.getenv("GMAIL_ADDRESS", "") if self._allow_send else ""
        self.app_password = os.getenv("GMAIL_APP_PASSWORD", "") if self._allow_send else ""
        self.server = None
        self.sent_count = 0
        self.fail_count = 0
        self.log = []

    def connect(self) -> bool:
        """Connect to Gmail SMTP with TLS."""
        if not self._allow_send or not self.email_address or not self.app_password:
            return False
        try:
            self.server = smtplib.SMTP('smtp.gmail.com', 587)
            self.server.starttls()
            self.server.login(self.email_address, self.app_password)
            print("[+] SMTP authenticated successfully")
            return True
        except Exception as e:
            print(f"[-] SMTP auth failed: {e}")
            return False

    def generate_pitch(self, lead: dict, *, use_ai: bool = False) -> tuple:
        """Generate personalized subject + body for a lead."""
        username = lead.get("Username", lead.get("username", "there"))
        company = lead.get("Company", lead.get("company", ""))
        website = lead.get("Website/Blog", lead.get("website", ""))

        # AI-generated pitch
        if self._allow_send and use_ai:
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
        if not self._allow_send or not self.server:
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

    @staticmethod
    def _read_recipients(csv_filepath):
        with open(csv_filepath, encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if not {"Email", "email"}.intersection(reader.fieldnames or ()):
                raise ValueError("input CSV requires an Email or email column")
            leads = list(reader)

        eligible = []
        for lead in leads:
            address = (lead.get("Email") or lead.get("email") or "").strip()
            local, separator, domain = address.partition("@")
            if (
                separator
                and local
                and domain
                and "@" not in domain
                and "noreply" not in address.lower()
                and "no-reply" not in address.lower()
                and not any(char.isspace() for char in address)
            ):
                eligible.append((address, lead))
        return len(leads), eligible

    def draft_campaign(self, csv_filepath, *, max_drafts=50, output=None):
        """Write a local report containing drafts generated from the CSV."""
        if max_drafts < 0:
            raise ValueError("maximum number of drafts must be non-negative")

        rows, eligible = self._read_recipients(csv_filepath)
        drafts = []
        for address, lead in eligible[:max_drafts]:
            subject, body = self.generate_pitch(lead)
            drafts.append({"email": address, "subject": subject, "body": body})

        report = {
            "mode": "draft",
            "input_rows": rows,
            "eligible_rows": len(eligible),
            "draft_count": len(drafts),
            "sent_count": 0,
            "drafts": drafts,
        }
        if output is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            output = f"campaign_drafts_{timestamp}.json"
        report_path = Path(output)
        with report_path.open("x", encoding="utf-8") as file:
            json.dump(report, file, ensure_ascii=False, indent=2)
            file.write("\n")
        return report_path

    def fire_campaign(self, csv_filepath: str, delay: int = 5, max_emails: int = 50):
        """Generate drafts unless the caller explicitly enabled sending."""
        if not self._allow_send:
            return self.draft_campaign(csv_filepath, max_drafts=max_emails)

        rows, eligible = self._read_recipients(csv_filepath)
        print(f"[*] {len(eligible)} valid targets out of {rows} total")
        print(f"[*] Delay: {delay}s between emails | Max: {max_emails}")

        targets = eligible[:max_emails]
        if not targets or not self.connect():
            return

        for i, (target, lead) in enumerate(targets):
            subject, body = self.generate_pitch(lead, use_ai=True)

            if self.send_email(target, subject, body):
                print(f"  [+] SENT ({i+1}/{len(targets)}): {target}")
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


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a local outreach draft report.")
    parser.add_argument("input", nargs="?", default="premium_b2b_leads.csv", help="lead CSV path")
    parser.add_argument("-o", "--output", help="path for a new JSON report")
    parser.add_argument("--max-drafts", type=int, default=50, help="maximum drafts to include")
    args = parser.parse_args(argv)
    engine = ColdEmailEngine()
    try:
        report = engine.draft_campaign(args.input, max_drafts=args.max_drafts, output=args.output)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        parser.exit(1, f"Could not write draft report: {error}\n")
    print(f"Draft report saved to {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
