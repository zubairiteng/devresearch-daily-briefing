"""Email sender supporting SMTP, Resend, SendGrid, and console dev mode."""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional
import httpx
from config.settings import settings

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self):
        self.provider = settings.MAIL_PROVIDER.lower()
        self.from_addr = settings.MAIL_FROM
        self.recipients = settings.recipient_list

    def send_email(
        self,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        to_addrs: Optional[List[str]] = None
    ) -> bool:
        recipients = to_addrs or self.recipients
        if not recipients:
            logger.warning("No email recipients configured; email not sent.")
            return False

        logger.info(f"Dispatching email via provider '{self.provider}' to {recipients}...")

        # 1. Console / Dev mode
        if self.provider == "console":
            print("\n" + "="*80)
            print(f"[CONSOLE EMAIL DISPATCH] From: {self.from_addr} | To: {', '.join(recipients)}")
            print(f"Subject: {subject}")
            print("="*80)
            if text_content:
                print(text_content[:600] + "\n...[truncated for console]...")
            else:
                print("[HTML Body Generated]")
            print("="*80 + "\n")
            return True

        # 2. Resend API
        if self.provider == "resend" and settings.RESEND_API_KEY:
            try:
                resp = httpx.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": self.from_addr,
                        "to": recipients,
                        "subject": subject,
                        "html": html_content,
                        "text": text_content
                    },
                    timeout=15.0
                )
                if resp.status_code in (200, 201):
                    logger.info(f"Email sent via Resend: {resp.json().get('id')}")
                    return True
                logger.error(f"Resend error: {resp.text}")
            except Exception as e:
                logger.error(f"Failed sending via Resend: {e}")

        # 3. SendGrid API
        elif self.provider == "sendgrid" and settings.SENDGRID_API_KEY:
            try:
                payload = {
                    "personalizations": [{"to": [{"email": r} for r in recipients]}],
                    "from": {"email": self.from_addr.split("<")[-1].replace(">", "").strip() or "daily@devresearch.local"},
                    "subject": subject,
                    "content": [
                        {"type": "text/html", "value": html_content}
                    ]
                }
                if text_content:
                    payload["content"].insert(0, {"type": "text/plain", "value": text_content})
                resp = httpx.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=15.0
                )
                if resp.status_code in (200, 202):
                    logger.info("Email sent via SendGrid.")
                    return True
                logger.error(f"SendGrid error: {resp.text}")
            except Exception as e:
                logger.error(f"Failed sending via SendGrid: {e}")

        # 4. Standard SMTP (Gmail App Password, etc.)
        elif self.provider == "smtp":
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = self.from_addr
                msg["To"] = ", ".join(recipients)

                if text_content:
                    msg.attach(MIMEText(text_content, "plain", "utf-8"))
                msg.attach(MIMEText(html_content, "html", "utf-8"))

                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20.0)
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(self.from_addr, recipients, msg.as_string())
                server.quit()
                logger.info(f"Email successfully delivered via SMTP to {recipients}")
                return True
            except Exception as e:
                logger.error(f"SMTP delivery failed: {e}")

        return False
