"""Send clear, easy-to-understand English briefing test email with layman terms to Prof. Zubair Ahmad."""
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
    
    # 1. Fetch fresh unemailed news items
    news_items = NewsRepository.get_unemailed_news(limit=15)
    if not news_items:
        print("No unemailed news found; falling back to latest news...")
        news_items = NewsRepository.get_latest_news(limit=15)
        
    jobs = JobRepository.get_jobs(include_not_eligible=False, limit=12)
    closing_soon = JobRepository.get_closing_soon_jobs(days_window=5)

    print("Synthesizing Easy English briefing with layman term definitions for Prof. Zubair Ahmad...")
    subject, html_body, txt_body = renderer.render_easy_english_digest(
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

    # Mark news items as emailed so they NEVER repeat!
    sent_ids = [n.id for n in news_items if n.id]
    if sent_ids:
        NewsRepository.mark_news_as_emailed(sent_ids)
        print(f"Marked {len(sent_ids)} news items as emailed in SQLite.")

    print(f"SUCCESS: Easy English Daily Briefing with Layman Explanations dispatched to {recip}!")

if __name__ == "__main__":
    main()
