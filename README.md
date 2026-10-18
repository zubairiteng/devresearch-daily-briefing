# DevResearch Daily Briefing

> **A production-ready personal briefing dashboard and automated daily digest engine.**
> Tailored for an MS Computer Science university lecturer, placement officer, NAVTTC skills trainer, and AI researcher based in Lahore / Gujranwala, Pakistan.

---

## Table of Contents
1. [Overview & Architecture](#overview--architecture)
2. [Tech Stack](#tech-stack)
3. [Quick Start (Local Development)](#quick-start-local-development)
4. [Docker & Container Deployment](#docker--container-deployment)
5. [GitHub Actions & GitHub Pages Deployment](#github-actions--github-pages-deployment)
6. [API Keys & Integrations Guide](#api-keys--integrations-guide)
7. [Remote & AI-Automation Jobs Watch](#remote--ai-automation-jobs-watch)
8. [Apply Assistant (Truthful CV & One-Click Help)](#apply-assistant-truthful-cv--one-click-help)
9. [Job Alert Emails Setup (IMAP)](#job-alert-emails-setup-imap)
10. [Configuration Guide](#configuration-guide)
11. [Job Eligibility Engine](#job-eligibility-engine)
12. [Dashboard Walkthrough](#dashboard-walkthrough)
13. [Running Tests](#running-tests)
14. [Antigravity Approval Policy Settings](#antigravity-approval-policy-settings)
15. [Project Structure](#project-structure)

---

## 1. Overview & Architecture

DevResearch Daily Briefing delivers a curated, actionable briefing every morning at **10:00 AM PKT (Asia/Karachi)** across five specialized categories:
1. **AI & LLM Industry News**: Frontier releases (OpenAI, Anthropic, Google DeepMind, DeepSeek, Meta Llama, Mistral, xAI, Qwen), hardware milestones, podcast takeaways, and tech-race developments.
2. **Software & Cloud Development**: Frameworks (React, Next.js, FastAPI, Python, Rust), cloud platforms (AWS, Azure, GCP, serverless, Kubernetes), and open-source tooling.
3. **Research Watch**: Quantum computing breakthroughs, NLP/LLM arXiv papers, and open publication opportunities with concrete **research gap** notes.
4. **Jobs Watch (Pakistan: Lahore & Gujranwala First)**: University faculty (Lecturer, Assistant Professor, Visiting, RA), placement/career services, NAVTTC/TEVTA skills programs, tech engineering, and PPSC/HEC public sector positions. Evaluated by a zero-guess **eligibility engine**.
5. **Remote & AI-Automation Jobs**: Worldwide and Pakistan-friendly roles across AI agents, LLM engineering, workflow automation (n8n, Zapier, Make, RPA), MLOps, and Python/AI development. Evaluates remote country exclusions (e.g., flags "US Only" vs "Worldwide").

```
                           ┌──────────────────────────────────────────────┐
                           │            Data Ingestion Layer              │
                           │  RSS Feeds • arXiv API • HN • Reddit • GitHub │
                           │  Podcasts • University Portals • PPSC/NAVTTC  │
                           │  RemoteOK • Remotive • Jobicy • LinkedIn IMAP│
                           └──────────────────────┬───────────────────────┘
                                                  │
                                                  ▼
                           ┌──────────────────────────────────────────────┐
                           │          Normalization & Dedup               │
                           │  URL canonicalization • Token Jaccard Sim    │
                           └──────────────────────┬───────────────────────┘
                                                  │
                                                  ▼
                           ┌──────────────────────────────────────────────┐
                           │         Relevance & Eligibility              │
                           │  Profile matching (0-100) • Hard rule engine │
                           │  Country restriction checks (Pakistan filter)│
                           │  Status: ELIGIBLE / MAYBE / NOT ELIGIBLE     │
                           └──────────────────────┬───────────────────────┘
                                                  │
                                                  ▼
                           ┌──────────────────────────────────────────────┐
                           │            Summarizer Adapter                │
                           │  Gemini • OpenAI • Anthropic • Heuristic     │
                           │  Strict human-colleague tone (No AI cliches) │
                           └──────────────────────┬───────────────────────┘
                                                  │
                     ┌────────────────────────────┴───────────────────────────┐
                     ▼                                                        ▼
         ┌───────────────────────┐                               ┌─────────────────────────┐
         │  SQLite Database WAL  │                               │    Digest Renderer      │
         │  News • Gaps • Jobs   │                               │    Responsive HTML      │
         └───────────┬───────────┘                               │    Plain-text Fallback  │
                     │                                           └────────────┬────────────┘
                     ▼                                                        │
         ┌───────────────────────┐                                            ▼
         │   FastAPI Dashboard   │                               ┌─────────────────────────┐
         │   Port 8000 Web UI    │                               │  Multi-Provider Mailer  │
         │   Apply Assistant     │                               │  SMTP • Resend • SendGrid│
         └───────────────────────┘                               └─────────────────────────┘
```

---

## 2. Tech Stack

- **Backend / API**: Python 3.11, [FastAPI](https://fastapi.tiangolo.com/), Uvicorn, Pydantic v2.
- **Database**: SQLite with Write-Ahead Logging (WAL) mode for concurrent read/write support (`data.db` committed back in GitHub Actions).
- **Scheduling**: [APScheduler](https://apscheduler.readthedocs.io/) running cron triggers in `Asia/Karachi` timezone with automatic retries and failure notification.
- **Content Parsing**: `feedparser`, `beautifulsoup4`, `lxml`, `httpx` (async HTTP/2 client).
- **Apply Assistant**: `pypdf`, `python-docx`, `reportlab` (ATS-tailored PDF generation), `playwright` (visible assisted browser prefill).
- **Template & Emailing**: `Jinja2` rendering responsive email HTML and UTF-8 plain-text. SMTP, Resend, and SendGrid adapters.
- **Frontend / Dashboard**: Single-page responsive interface styled with Tailwind CSS, Lucide icons, and zero external build tooling required.

---

## 3. Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Git

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/devresearch/daily-briefing.git
cd daily-briefing
```

# Create and activate virtual environment
python -m venv venv

# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Initialize Configuration
```bash
# Copy template environment file
cp .env.example .env
```
Edit `.env` as needed. By default, it operates in `MAIL_PROVIDER=console` and `LLM_PROVIDER=heuristic`, allowing full execution without requiring any paid API keys.

### 4. Run the Dashboard & Web Server
```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser at **`http://127.0.0.1:8000`** to view the live dashboard!

### 5. Execute an Immediate Pipeline Run (CLI)
```bash
python run_pipeline.py
```
This triggers the live pipeline, downloads latest stories and Pakistan/Remote jobs, and writes a real `sample_digest.html` to disk.

---

## 4. Docker & Container Deployment

### Running with Docker Compose
```bash
# Build and run containerized server
docker-compose up -d --build

# View real-time container logs
docker-compose logs -f
```
The application will be accessible on `http://localhost:8000`. Database state and YAML configurations are persisted on your host volume.

---

## 5. GitHub Actions & GitHub Pages Deployment

The automated daily pipeline and public mirror are configured in [`.github/workflows/daily.yml`](.github/workflows/daily.yml).

### Schedule & Timezone Conversion
GitHub Actions uses UTC cron schedules:
- **Pakistan Standard Time (PKT)**: `UTC+5`
- **10:00 AM PKT** = **05:00 AM UTC** (`cron: '0 5 * * *'`).
- Also supports manual execution anytime via `workflow_dispatch`.

### State Persistence & Deduplication
To prevent stale feeds and duplicate job alerts:
1. `data.db` is restored from the repository before the pipeline starts.
2. The pipeline runs and enriches `devresearch.db`.
3. Changes are committed back to `data.db` using `git diff --staged --quiet || git commit -m "chore: persist data.db after daily briefing [skip ci]"`.

### Sanitized Public Mirror (GitHub Pages)
- **Why GitHub Pages?**: Deploys in one step using standard Actions (`actions/deploy-pages@v4`), has zero hosting costs, and requires no external third-party API keys or accounts (unlike Vercel or Cloudflare Pages).
- **Privacy Enforcement**: The static dashboard export script (`scripts/export_static_dashboard.py`) strips all personal CV data, contact numbers, email addresses, and private job tracker notes. The public mirror serves exclusively public news, research gaps, and public job vacancies.

### Automated Setup with GitHub CLI (`gh`):
```bash
# 1. Authenticate with GitHub
gh auth login

# 2. Create the private repository and push main
gh repo create devresearch-daily-briefing --private --source=. --remote=origin --push

# 3. Automatically set repository secrets from your local .env:
gh secret set SMTP_USER --body "your_email@gmail.com"
gh secret set SMTP_PASSWORD --body "your_16_char_app_password"
gh secret set MAIL_RECIPIENTS --body "your_email@gmail.com"
gh secret set GEMINI_API_KEY --body "your_gemini_key"
gh secret set LLM_PROVIDER --body "gemini"
gh secret set MAIL_PROVIDER --body "smtp"

# 4. Trigger a test workflow run
gh workflow run daily.yml

# 5. Check run status
gh run list
```

---

## 6. API Keys & Integrations Guide

### A. Google Gemini API (Recommended for LLM Summaries)
1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API key** and generate a new key.
3. In `.env`:
   ```env
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

### B. OpenAI API
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys).
2. Generate a secret key.
3. In `.env`:
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-...
   ```

### C. Anthropic Claude API
1. Visit [Anthropic Console](https://console.anthropic.com/).
2. Create an API key.
3. In `.env`:
   ```env
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-...
   ```

### D. SMTP with Gmail (Free Email Dispatch)
1. Go to your [Google Account Security](https://myaccount.google.com/security).
2. Enable **2-Step Verification**.
3. Search for **App passwords**.
4. Create an App password named "DevResearch Briefing". Copy the 16-character code.
5. In `.env`:
   ```env
   MAIL_PROVIDER=smtp
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_16_char_app_password
   SMTP_USE_TLS=true
   MAIL_RECIPIENTS=your_email@gmail.com
   ```

### E. Resend (Modern Transactional Email)
1. Sign up at [Resend.com](https://resend.com/).
2. Create an API key and verify your domain.
3. In `.env`:
   ```env
   MAIL_PROVIDER=resend
   RESEND_API_KEY=re_...
   MAIL_FROM="DevResearch Daily <briefing@yourdomain.com>"
   ```

---

## 7. Remote & AI-Automation Jobs Watch

DevResearch includes a dedicated feed and digest category specifically targeting high-demand modern AI and automation roles:
- **Roles Tracked**: Agentic AI / AI Agents, LLM Engineers, Prompt Engineers, Workflow Automation (n8n, Zapier, Make), RPA, MLOps, Data Science, and Python/AI developers.
- **Priority Ranking**: Worldwide remote and Pakistan-friendly remote roles rank highest.
- **Country Restriction Evaluation**:
  - The fetcher automatically inspects location and country eligibility clauses.
  - If a job specifies "US Only", "EU Only", "UK Only", or "North America Only", it is flagged and marked `NOT ELIGIBLE: Excludes Pakistan (Location: US Only)`.
  - Roles open to "Worldwide", "Anywhere", "EMEA", "APAC", or "Pakistan" receive high relevance boosts and are marked `ELIGIBLE` or `MAYBE` (if age/unspecified).
- **Zero-Scraping Compliance**: No illegal scraping of LinkedIn or protected portals. Remote jobs are fetched legally via official APIs and RSS feeds:
  - [RemoteOK API](https://remoteok.com/api)
  - [Remotive Public API](https://remotive.com/api/remote-jobs)
  - [Jobicy API](https://jobicy.com/api/v2/remote-jobs)
  - [We Work Remotely RSS](https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss)
  - LinkedIn Job Alerts parsed directly from your own email inbox via IMAP.

---

## 8. Apply Assistant (Truthful CV & One-Click Help)

The Apply Assistant helps you prepare tailored, truthful job applications without ever taking control away from you:

### 1. Zero-Fabrication Guarantee
- Drop your real CV (`.pdf` or `.docx`) into the gitignored `private/` folder.
- The assistant extracts your verified profile: degrees, years of teaching, placement and NAVTTC experience, publications, and specific technical skills.
- **Fact-grounded generation**: All generated cover letters (150–250 words) use *only* the facts in your CV. If a job requires a skill you do not have, the assistant highlights it under **Missing Skills / Gap** instead of making false claims.

### 2. ATS-Tailored PDF CV Generation
- Powered by `ReportLab`, generating clean, single-page, ATS-friendly PDFs formatted to `private/generated/CV_<Company>_<Role>.pdf`.
- Reorders your verified skills and highlights projects directly matching the target job description.

### 3. Assisted Desktop Browser Fill (Playwright)
- Clicking **"Open in Browser with Assistant"** launches a visible Chromium browser (`headless=False`).
- Safely pre-fills application input fields (Name, Email, Phone, LinkedIn, Location, Cover Letter) where accessible.
- Displays a prominent amber guidance banner at the top of the browser: **" DevResearch Apply Assistant: Form pre-filled. Please review and click Submit yourself."**
- **Strict safety rule**: The assistant **never** auto-submits forms. You review every field and click the final "Submit" button.

### 4. Direct Email Applications
- For university, government, or employer postings that require sending an email, clicking **"Send Application Email"** opens a review modal and dispatches your tailored cover letter and attached tailored PDF CV via your configured SMTP mailer, logging the application stage as `Applied`.

---

## 9. Job Alert Emails Setup (IMAP)

Many Pakistani job boards (Rozee.pk, Indeed Pakistan, LinkedIn Jobs) offer personalized daily email alerts. You can configure the built-in IMAP parser to extract jobs directly from these alert emails:

### How to set up job alerts:
1. **Rozee.pk**:
   - Create alerts for: `Lecturer Computer Science`, `Placement Officer`, `NAVTTC Trainer`, `AI Engineer`.
   - City: `Lahore`, `Gujranwala`.
2. **Indeed Pakistan**:
   - Query: `Lecturer Computer Science` in `Lahore` & `Gujranwala`. Select "Get job alerts for this search".
3. **LinkedIn Jobs**:
   - Search: `University Lecturer` or `Career Placement Officer` in `Lahore, Punjab, Pakistan` and `Remote AI Engineer`. Click "Set Alert".

### Configuring IMAP Parser:
In your `.env` file:
```env
IMAP_ENABLED=true
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USER=your_email@gmail.com
IMAP_PASSWORD=your_gmail_app_password
IMAP_FOLDER=INBOX
```
The fetcher automatically identifies unread messages containing "Job Alert", parses the job cards, runs the eligibility engine, and records them in your dashboard.

---

## 10. Configuration Guide

### Customizing User Profile (`profile.yaml`)
You can edit `profile.yaml` directly or update it from the **Settings** tab in the dashboard.
```yaml
personal:
  name: "Dr./Prof. Dev Researcher"
  birth_date: "1998-05-15"  # Automatically recalculates current age every year

education:
  degree: "MS Computer Science"
  level: "MS/MPhil"
  field: "Computer Science"

experience_years:
  teaching: 3.5
  industry: 2.5
  placement_and_training: 2.0
  total: 4.5

locations:
  tier_1:
    - "Lahore"
    - "Gujranwala"
  tier_2:
    - "Sialkot"
    - "Gujrat"
    - "Islamabad"
  tier_3:
    - "Remote"
```
> **Automatic Recalculation**: Whenever `profile.yaml` is saved through the dashboard, all stored jobs are instantly re-evaluated against the new age, degree, or experience levels!

### Adding / Editing Sources (`sources.yaml`)
To add a new RSS feed, podcast, or university career portal, edit `sources.yaml`:
```yaml
news:
  rss_feeds:
    - name: "My New Tech Blog"
      category: "software_cloud"
      url: "https://example.com/feed.xml"
      enabled: true

jobs:
  pakistan_sources:
    - name: "New Lahore University"
      type: "university_portal"
      city: "Lahore"
      url: "https://newuniv.edu.pk/careers"
      enabled: true
  remote_sources:
    - name: "RemoteOK AI Feed"
      type: "remote_api"
      url: "https://remoteok.com/api"
      enabled: true
```

### Changing Delivery Time & Timezone
In `.env`:
```env
TIMEZONE=Asia/Karachi
DIGEST_TIME="10:00"
```
Or adjust it anytime from the dashboard Settings tab.

---

## 11. Job Eligibility Engine

The engine strictly tests ads against your user profile and assigns one of three statuses:
- **`ELIGIBLE`**: Age, degree level, experience requirements, and location (Pakistan / Worldwide) are fully satisfied.
- **`MAYBE`**: Criteria is unspecified (e.g., age limit not stated) or marginally matches.
- **`NOT ELIGIBLE`**: Hard failure (e.g. mandatory PhD required, age limit exceeded, required experience exceeds background, or geographic restriction excludes Pakistan).

### Zero-Guessing Rule
Every status produces an explanatory human sentence:
> `Max age 35, you are 28: OK. MS/MPhil required, you have MS/MPhil: OK. 2.0 yrs required, you have 3.5 yrs: OK.`

If an ad omits an age limit or qualification, the engine outputs `"Not mentioned"` and marks it `MAYBE`.

---

## 12. Dashboard Walkthrough

Visit `http://localhost:8000`:
- **Today Tab**: Digest grouped into AI & LLM, Dev & Cloud, Research Watch, and Remote & AI Jobs with score badges, "Why it matters to you", and "Read later" toggles.
- **History Tab**: Search across past items with category, source, score, and bookmark filters.
- **Research Gaps Board**: Tracks publication opportunities, open challenges, and status tags (`open`, `investigating`, `published`).
- **Jobs Watch Tab**: Filter jobs by city (Lahore / Gujranwala first), eligibility status, and application stage. Features an application tracker (`Saved` &rarr; `Applied` &rarr; `Interview` &rarr; `Rejected` &rarr; `Offer`).
- **Apply Assistant Modal**: Click "Apply Assistant" on any job card to view matched vs missing skills, preview and edit your tailored cover letter, download an ATS PDF CV, or launch assisted desktop browser filling.
- **Settings Tab**: Live editor for profile qualifications, age, experience, schedule, and mail options. Includes one-click **"Send test email now"** and **"Run pipeline now"** buttons.

---

## 13. Running Tests

Run the comprehensive pytest suite verifying deduplication, scoring, job eligibility, remote country restrictions, cover letter truthfulness, email rendering, and API routes:
```bash
python -m pytest tests/ -v
```
All **25 unit tests** run and pass in under 2 seconds without external network dependencies.

---

## 14. Antigravity Approval Policy Settings

If you prefer Antigravity to run commands and edit files in this project workspace without prompting for individual approvals:
1. In the Antigravity UI, navigate to **Settings** (or press `Ctrl+,`).
2. Go to **Agent > Command Execution & Tool Permissions**.
3. Under **Workspace Execution Policy**, select:
   - **Terminal Commands**: Change from `Prompt for each command` to **`Always Allow in Workspace`** (or add `python`, `git`, `gh`, `pytest` to the Allowed Commands list).
   - **File Modifications**: Set to **`Auto-approve within workspace`**.
4. This ensures future autonomous runs execute without interruptions.

---

## 15. Project Structure

```
daily-briefing/
├── config/
│   ├── settings.py              # Pydantic Settings (.env)
│   ├── profile_loader.py        # profile.yaml loader & dynamic age calculator
│   └── sources_loader.py        # sources.yaml schema loader & validator
├── database/
│   ├── connection.py            # SQLite connection with WAL mode & schema init
│   ├── models.py                # Pydantic data schemas
│   └── news_repo.py             # News & Research SQLite repository
├── fetchers/
│   ├── base.py                  # Base fetcher interface & RawItem model
│   ├── rss_fetcher.py           # RSS/Atom fetcher with HTML cleanup
│   ├── arxiv_fetcher.py         # arXiv API fetcher (cs.CL, cs.AI, quant-ph)
│   ├── hn_fetcher.py            # Hacker News Firebase API fetcher
│   ├── reddit_fetcher.py        # Reddit JSON fetcher (r/MachineLearning, r/LocalLLaMA)
│   ├── github_fetcher.py        # GitHub releases API fetcher
│   └── podcast_fetcher.py       # Podcast RSS fetcher with takeaways
├── processors/
│   ├── deduplicator.py          # Canonical URL & token Jaccard title similarity
│   ├── classifier.py            # Category classification engine
│   └── scorer.py                # 0-100 relevance scoring against user profile
├── summarizer/
│   ├── base.py                  # SummaryResult schema
│   ├── heuristic.py             # Rule-based fallback enforcing human colleague tone
│   └── llm_adapter.py           # Gemini, OpenAI, Anthropic LLM adapter
├── jobs/
│   ├── fetchers/
│   │   ├── base_job_fetcher.py
│   │   ├── indeed_fetcher.py    # Indeed PK RSS queries
│   │   ├── university_fetcher.py# PU, UET, GIFT, UOG, FAST portals
│   │   ├── govt_skills_fetcher.py# PPSC, NAVTTC, PSDA portals
│   │   ├── imap_fetcher.py      # IMAP job alert email parser
│   │   └── remote_fetcher.py    # RemoteOK, Remotive, WWR & country eligibility
│   ├── parser/
│   │   └── extractor.py         # Regex & heuristic extractor (age, qual, exp, date)
│   ├── eligibility/
│   │   └── engine.py            # Strict ELIGIBLE / MAYBE / NOT ELIGIBLE evaluator
│   ├── apply_assistant/
│   │   ├── cv_parser.py         # Truthful CV parser from private/ (.pdf, .docx)
│   │   ├── cover_letter.py      # Fact-grounded 150-250 word cover letter generator
│   │   ├── cv_generator.py      # ReportLab ATS-tailored PDF CV generator
│   │   └── browser_assist.py    # Visible Playwright desktop browser assist
│   ├── store/
│   │   └── job_repo.py          # Job deduplication, source merging, and tracker
│   └── pipeline.py              # Jobs pipeline orchestrator
├── mailer/
│   ├── renderer.py              # Jinja2 template renderer for HTML & plain text
│   ├── sender.py                # SMTP, Resend, SendGrid, and Console sender
│   └── templates/
│       ├── digest.html          # Responsive dark-mode aware email template
│       ├── digest.txt           # Plain-text email fallback
│       └── error_alert.html     # Failure notification template
├── scheduler/
│   └── runner.py                # APScheduler daily 10:00 AM runner with retries
├── api/
│   ├── main.py                  # FastAPI application entrypoint
│   └── routes.py                # REST API routers for dashboard & triggers
├── frontend/
│   └── index.html               # Modern responsive web dashboard
├── scripts/
│   └── export_static_dashboard.py # Builds sanitized static mirror for GitHub Pages
├── tests/
│   ├── test_news_dedup.py
│   ├── test_relevance_scoring.py
│   ├── test_job_eligibility.py
│   ├── test_job_dedup.py
│   ├── test_email_rendering.py
│   ├── test_api_endpoints.py
│   └── test_remote_and_assistant.py
├── .github/workflows/
│   └── daily.yml                # GitHub Actions daily cron (05:00 UTC = 10:00 AM PKT)
├── Dockerfile                   # Production container specification
├── docker-compose.yml           # Docker compose orchestrator
├── profile.yaml                 # User profile configuration
├── sources.yaml                 # News, research, Pakistani & Remote job sources
├── .env.example                 # Environment variable template
├── run_pipeline.py              # CLI entrypoint for pipeline runs
└── requirements.txt             # Python dependencies
```

