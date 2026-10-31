"""Send mature, executive-level Urdu daily briefing test email to Prof. Zubair Ahmad."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from database.connection import init_db
from database.news_repo import NewsRepository
from jobs.store.job_repo import JobRepository
from mailer.renderer import DigestRenderer

def main():
    print("Initializing DevResearch Database...")
    init_db()

    renderer = DigestRenderer()
    news_items = NewsRepository.get_latest_news(limit=20)
    jobs = JobRepository.get_jobs(include_not_eligible=False, limit=12)
    closing_soon = JobRepository.get_closing_soon_jobs(days_window=5)

    print("Synthesizing mature Urdu briefing for Prof. Zubair Ahmad...")
    subject, html_body, txt_body = renderer.render_urdu_digest(
        news_items=news_items,
        jobs=jobs,
        closing_soon=closing_soon
    )

    user = settings.SMTP_USER
    pwd = settings.SMTP_PASSWORD
    recip = settings.MAIL_RECIPIENTS

    print(f"Connecting to SMTP {settings.SMTP_HOST}:{settings.SMTP_PORT} as {user}...")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"DevResearch Daily <{user}>"
    msg["To"] = recip

    msg.attach(MIMEText(txt_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=25.0)
    server.starttls()
    server.login(user, pwd)
    server.sendmail(user, [recip], msg.as_string())
    server.quit()

    print(f"SUCCESS: Rich Urdu Daily Briefing successfully dispatched to {recip}!")

if __name__ == "__main__":
    main()
