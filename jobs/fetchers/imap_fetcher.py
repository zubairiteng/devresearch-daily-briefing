"""IMAP email parser for Rozee, Indeed, and LinkedIn job alerts."""
import email
import imaplib
import logging
from datetime import datetime, timezone
from email.header import decode_header
from typing import List
from bs4 import BeautifulSoup

from .base_job_fetcher import BaseJobFetcher, RawJob
from config.settings import settings
from config.sources_loader import ImapAlertConfig

logger = logging.getLogger(__name__)


def decode_str(header_val: str) -> str:
    if not header_val:
        return ""
    decoded_fragments = decode_header(header_val)
    parts = []
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            parts.append(fragment.decode(encoding or "utf-8", errors="replace"))
        else:
            parts.append(str(fragment))
    return "".join(parts)


class ImapJobAlertFetcher(BaseJobFetcher):
    name = "ImapJobAlertFetcher"

    def __init__(self, config: ImapAlertConfig):
        self.config = config

    async def fetch(self) -> List[RawJob]:
        # Only execute if IMAP is enabled in config and settings has user/pass
        if not settings.IMAP_ENABLED or not settings.IMAP_USER or not settings.IMAP_PASSWORD:
            logger.info("IMAP job alert fetcher is disabled or unconfigured; skipping.")
            return []

        jobs: List[RawJob] = []
        try:
            mail = imaplib.IMAP4_SSL(settings.IMAP_SERVER, settings.IMAP_PORT)
            mail.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
            mail.select(self.config.folder or "INBOX")

            # Search recent emails matching alerts
            status, messages = mail.search(None, '(UNSEEN SUBJECT "Job Alert")')
            if status != "OK" or not messages[0]:
                mail.logout()
                return []

            msg_ids = messages[0].split()[-10:]  # Take latest 10
            for msg_id in msg_ids:
                status, data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                subject = decode_str(msg.get("Subject", ""))
                sender = decode_str(msg.get("From", ""))

                body_text = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() in ("text/plain", "text/html"):
                            payload = part.get_payload(decode=True)
                            if payload:
                                soup = BeautifulSoup(payload.decode("utf-8", errors="replace"), "html.parser")
                                body_text += " " + soup.get_text()
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        soup = BeautifulSoup(payload.decode("utf-8", errors="replace"), "html.parser")
                        body_text = soup.get_text()

                # Basic extraction from alert email body
                clean_body = " ".join(body_text.split())[:1000]
                jobs.append(
                    RawJob(
                        title=f"Alert: {subject[:70]}",
                        organization=sender.split("<")[0].strip() or "Job Alert Portal",
                        city="Lahore",
                        url=f"email://{msg_id.decode()}",
                        source_name="Email Alert (IMAP)",
                        description=clean_body,
                        apply_link="https://www.linkedin.com/jobs/",
                        fetched_at=datetime.now(timezone.utc)
                    )
                )

            mail.logout()
            logger.info(f"Fetched {len(jobs)} jobs from IMAP email alerts")
        except Exception as e:
            logger.warning(f"Error fetching IMAP job alerts: {e}")

        return jobs
