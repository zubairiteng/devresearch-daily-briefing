"""Send test verification email."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings

user = settings.SMTP_USER
pwd = settings.SMTP_PASSWORD
recip = settings.MAIL_RECIPIENTS

print(f"Connecting to SMTP {settings.SMTP_HOST}:{settings.SMTP_PORT} as {user}...")

msg = MIMEMultipart("alternative")
msg["Subject"] = " DevResearch Daily Briefing - Test Verification Email"
msg["From"] = f"DevResearch Daily <{user}>"
msg["To"] = recip

html_body = f"""
<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
  <div style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); padding: 24px 30px; color: #ffffff;">
    <h1 style="margin: 0; font-size: 22px;"> DevResearch Daily Briefing</h1>
    <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px;">Email Delivery System Test</p>
  </div>
  <div style="padding: 24px 30px; color: #334155;">
    <h2 style="color: #0f172a; font-size: 18px; margin-top: 0;">Assalam-o-Alaikum, Prof. Zubair!</h2>
    <p style="font-size: 15px; line-height: 1.6;">
      This email confirms that your SMTP delivery setup and Google App Password are <strong>100% connected and operational</strong>.
    </p>
    <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 14px 18px; margin: 20px 0;">
      <p style="margin: 0; color: #166534; font-weight: 600;"> Status: Fully Connected</p>
      <p style="margin: 5px 0 0 0; color: #15803d; font-size: 14px;">Recipient: <strong>{recip}</strong></p>
      <p style="margin: 2px 0 0 0; color: #15803d; font-size: 14px;">Delivery Schedule: <strong>Daily at 10:00 AM PKT</strong></p>
    </div>
    <p style="font-size: 14px; color: #64748b; line-height: 1.5;">
      Your automated briefing covers:
    </p>
    <ul style="font-size: 14px; color: #475569; line-height: 1.6;">
      <li><strong>AI & LLM Industry News:</strong> Frontier models, hardware, podcasts</li>
      <li><strong>Software & Cloud:</strong> Web, AWS/Azure/GCP, developer tools</li>
      <li><strong>Research Watch:</strong> Quantum computing, NLP arXiv papers & research gaps</li>
      <li><strong>Jobs Watch (Pakistan):</strong> Lahore & Gujranwala university faculty & tech roles</li>
      <li><strong>Remote & AI Jobs:</strong> Worldwide remote automation & agentic AI positions</li>
    </ul>
  </div>
  <div style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 14px 30px; font-size: 12px; color: #94a3b8; text-align: center;">
    DevResearch Daily Briefing Automation &bull; IISAT University &bull; Automated via GitHub Actions
  </div>
</div>
"""

msg.attach(MIMEText(html_body, "html", "utf-8"))

server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20.0)
server.starttls()
server.login(user, pwd)
server.sendmail(user, [recip], msg.as_string())
server.quit()

print(f"SUCCESS: Test email successfully sent to {recip}!")
