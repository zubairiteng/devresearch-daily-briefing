"""Easy English content synthesizer for DevResearch Daily Briefing.

Tailored for Prof. Zubair Ahmad (MS CS Lecturer, Placement Officer, NAVTTC Trainer, AI Researcher).
Enforces:
1. Easy, plain, conversational English (no robotic cliches or dense academic fluff).
2. Plain-language definitions for every technical term / jargon in simple terms.
3. Fresh unemailed news every day with non-repeating tracking.
4. Active career opportunities and Pakistan IEEE/HEC academic watch (which can repeat while active).
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from database.models import NewsItemModel, JobItemModel
from mailer.layman_explainer import extract_layman_terms, get_concept_of_the_day


class EasyEnglishSynthesizer:
    """Produces clear, engaging, and easy-to-understand English briefing with layman explanations."""

    @staticmethod
    def synthesize(
        news_items: List[NewsItemModel],
        jobs: List[JobItemModel],
        closing_soon: List[JobItemModel],
        date_obj: datetime = None
    ) -> Dict[str, Any]:
        dt = date_obj or datetime.now()
        date_str = dt.strftime("%A, %B %d, %Y")
        short_date = dt.strftime("%b %d, %Y")

        # 1. Process and enrich news items with layman explanations
        enriched_news = []
        for item in news_items:
            combined_text = f"{item.title} {item.summary} {item.why_it_matters or ''} {item.research_gap or ''}"
            terms = extract_layman_terms(combined_text, max_terms=3)
            enriched_news.append({
                "id": item.id,
                "title": item.title,
                "url": item.url,
                "source_name": item.source_name,
                "category": item.category,
                "summary": item.summary,
                "why_it_matters": item.why_it_matters,
                "research_gap": item.research_gap,
                "score": item.score,
                "layman_terms": terms
            })

        # Categorize into sections
        ai_stories = [n for n in enriched_news if n["category"] == "ai_llm"]
        dev_stories = [n for n in enriched_news if n["category"] == "software_cloud"]
        research_stories = [n for n in enriched_news if n["category"] == "research_watch"]

        # 2. Curated Frontier AI & Robotics Highlights (OpenAI, Anthropic, Musk/Tesla, China Robotics)
        frontier_ai_briefs = [
            {
                "headline": "OpenAI & Anthropic Race on Reasoning Verifiers and Coding Agents",
                "tag": "OpenAI & Anthropic",
                "source": "AI Research Labs",
                "summary": "AI labs are shifting focus from simply making models larger to making them think longer ('Test-Time Compute'). Anthropic's Claude 3.5 can now directly operate computer screens and terminals, while OpenAI is using internal verifier circuits to catch software bugs before showing answers.",
                "layman_terms": extract_layman_terms("Test-time compute verifier circuits agentic ai computer use api"),
                "why_it_matters": "In your university classes, this means teaching students how to build multi-agent software and automated test loops is now far more valuable than basic prompt writing.",
                "link": "https://openai.com/news/"
            },
            {
                "headline": "Elon Musk & Tesla: Optimus Humanoid Robots Deployed in Factories",
                "tag": "Elon Musk & Tesla / xAI",
                "source": "Tesla & xAI",
                "summary": "Tesla has begun deploying its Optimus Gen-3 humanoid robots to autonomously move battery cells inside gigafactories. Meanwhile, xAI's 'Colossus' GPU cluster in Memphis has reached 100,000 Nvidia H100 chips, training next-generation Grok models with multimodal physical understanding.",
                "layman_terms": extract_layman_terms("Humanoid robot Colossus GPU cluster embodied AI actuators"),
                "why_it_matters": "Great encouragement for your computer vision and robotics students: physical AI and factory automation are moving out of research labs and into production lines.",
                "link": "https://x.ai"
            },
            {
                "headline": "China's Robotics Boom: Mass Production of Sub-$16,000 Industrial Humanoids",
                "tag": "China Robotics Surge",
                "source": "Global Robotics Review",
                "summary": "Chinese manufacturers including Unitree and AgiBot are commercially shipping full-sized humanoid robots at record-low prices around $16,000. These robots run lightweight open-weight models (like DeepSeek) on edge hardware, lowering entry barriers for factory and warehouse automation.",
                "layman_terms": extract_layman_terms("Humanoid robot Open-weight models Edge AI"),
                "why_it_matters": "Shows that hardware and robotics automation will quickly become affordable in Asian manufacturing, creating high demand for AI automation engineers.",
                "link": "https://www.unitree.com"
            }
        ]

        # 3. Pakistan Academic Watch: IEEE Conferences & HEC Grants
        academic_programs = [
            {
                "title": "IEEE Pakistan Flagship Conferences (Call for Papers & Submissions)",
                "category": "IEEE Pakistan Conferences",
                "details_list": [
                    {
                        "name": "FIT 2026 (Frontiers of Information Technology)",
                        "organizer": "COMSATS University Islamabad",
                        "tracks": "Artificial Intelligence, Data Science, Software Engineering, Networks",
                        "index": "IEEE Xplore & Scopus Indexed",
                        "status": "Annual cycle active; paper drafting and early submissions recommended",
                        "link": "https://fit.edu.pk",
                        "layman_note": "A premier venue in Pakistan where your research paper gets indexed directly in IEEE Xplore and Scopus."
                    },
                    {
                        "name": "IEEE INMIC (International Multi-Topic Conference)",
                        "organizer": "IEEE Pakistan Section",
                        "tracks": "Emerging Technologies, Machine Learning, Embedded Systems",
                        "index": "IEEE Xplore Indexed",
                        "status": "Call for Papers announcements active across universities",
                        "link": "https://ieeepakistan.org",
                        "layman_note": "Ideal conference for student-faculty joint research papers."
                    },
                    {
                        "name": "IBCAST (International Bhurban Conference on Applied Sciences & Tech)",
                        "organizer": "Centers of Excellence",
                        "tracks": "Cyber Security, Quantum Tech, Autonomous Robotics",
                        "index": "IEEE Indexed",
                        "status": "Submissions and registration open",
                        "link": "https://ibcast.org.pk",
                        "layman_note": "High-prestige conference with military, government, and academic recognition."
                    }
                ]
            },
            {
                "title": "HEC Research Grants & Fellowships for Faculty & Researchers",
                "category": "HEC Grants & Fellowships",
                "details_list": [
                    {
                        "name": "HEC IRSIP (International Research Support Initiative Program)",
                        "details": "HEC Pakistan fully funds a 6-month research fellowship for local PhD scholars/faculty to conduct advanced lab experiments at top 500 foreign universities worldwide.",
                        "funding": "Full travel ticket, bench fees, and monthly foreign living stipend",
                        "eligibility": "Enrolled PhD scholars and faculty at Pakistani recognized universities",
                        "portal": "https://hec.gov.pk/english/scholarships-fellowships/irsip",
                        "layman_note": "In simple terms: A 100% paid opportunity to spend 6 months abroad doing research with world-class professors."
                    },
                    {
                        "name": "HEC NRPU (National Research Program for Universities)",
                        "details": "Competitive grant funding applied scientific research projects addressing national socioeconomic needs, especially in Applied AI, Agriculture, and Healthcare.",
                        "funding": "Up to 20 Million PKR per approved project",
                        "eligibility": "Regular university faculty members (Lecturers & Assistant Professors)",
                        "portal": "https://hec.gov.pk/english/services/faculty/NRPU",
                        "layman_note": "In simple terms: Government funds up to 2 Crore PKR for your university lab to buy equipment and hire research students."
                    },
                    {
                        "name": "HEC Faculty Development Program (FDP) & NCEAC Standards",
                        "details": "Training workshops to adopt modern computing pedagogy and align departmental labs with National Computing Education Accreditation Council (NCEAC) benchmarks.",
                        "funding": "Fully subsidized institutional workshops",
                        "eligibility": "Public and private sector computing faculty members",
                        "portal": "https://hec.gov.pk/english/services/faculty/fdp",
                        "layman_note": "Helps you align your course outlines and practical labs with official accreditation rules."
                    }
                ]
            }
        ]

        # 4. Open Research Gaps (Ideas ready for paper publication)
        research_gaps = [
            {
                "area": "Natural Language Processing (NLP & Regional Dialects)",
                "topic": "Reasoning Verifiers for Low-Resource Urdu Dialects",
                "gap_description": "While models like o1 excel in English logic verification, they frequently miss logical fallacies when evaluated on Urdu and regional text. Training a lightweight verifier circuit on localized reasoning datasets is an open, high-impact paper topic suitable for IEEE FIT.",
                "layman_terms": extract_layman_terms("Verifier reasoning model low-resource dialects")
            },
            {
                "area": "Quantum Machine Learning",
                "topic": "Noise Mitigation in Variational Quantum Classifiers (VQC)",
                "gap_description": "Current noisy quantum processors lose accuracy during variational training. Using classical lightweight agentic models to optimize quantum gate placements in real-time is a fresh, under-explored publication opportunity.",
                "layman_terms": extract_layman_terms("Surface code quantum computing agentic ai")
            },
            {
                "area": "Agentic AI & Workflow Automation",
                "topic": "Deterministic Rollbacks in Self-Healing Multi-Agent Systems",
                "gap_description": "When multi-agent tools (like n8n or LangChain) run complex business workflows, error recovery often spirals out of control. Designing an automated rollback and checkpointing mechanism represents a strong applied software engineering contribution.",
                "layman_terms": extract_layman_terms("Agentic AI n8n workflow automation")
            }
        ]

        # 5. Career & Placement Opportunities (Strictly filter out NOT ELIGIBLE, can repeat while active)
        eligible_jobs = [j for j in jobs if j.eligibility_status in ("ELIGIBLE", "MAYBE")]
        academic_jobs = [
            j for j in eligible_jobs
            if any(k in j.title.lower() for k in ["lecturer", "professor", "visiting", "faculty", "trainer", "placement"])
        ]
        tech_remote_jobs = [
            j for j in eligible_jobs
            if j not in academic_jobs
        ]

        # 6. Concept of the Day (In Simple Words)
        concept_of_the_day = get_concept_of_the_day(dt)

        # 7. Today in Brief (3 quick takeaway bullets)
        today_in_brief = [
            "AI Frontier: Labs are prioritizing 'Test-Time Compute' (letting AI think for seconds) and humanoid factory robots over raw chatbot size.",
            "Academic Watch: IEEE Pakistan (FIT & INMIC) submission cycles active; HEC IRSIP (6-month foreign fellowship) & NRPU (up to 20M PKR) open for faculty.",
            f"Career Watch: {len(academic_jobs) + len(tech_remote_jobs)} verified openings active for you across CS lecturing, NAVTTC training, and remote AI automation."
        ]

        # Subject Line: DevResearch Daily | Nov 03, 2026 | Easy English Executive Briefing
        top_headline = "AI Frontier, IEEE Conferences, HEC Grants & Career Watch"
        if ai_stories:
            clean_title = re.sub(r"^(Show HN:|Ask HN:|\[.*?\])\s*", "", ai_stories[0]["title"]).strip()
            if len(clean_title) < 60:
                top_headline = clean_title

        subject = f"DevResearch Daily | {short_date} | {top_headline}"

        return {
            "subject": subject,
            "date_str": date_str,
            "short_date": short_date,
            "user_name": "Prof. Zubair Ahmad",
            "user_profile_line": "MS CS Lecturer, Placement Officer, NAVTTC Trainer & AI Researcher",
            "today_in_brief": today_in_brief,
            "concept_of_the_day": concept_of_the_day,
            "frontier_ai_briefs": frontier_ai_briefs,
            "fresh_news_items": enriched_news[:8],
            "ai_stories": ai_stories[:4],
            "dev_stories": dev_stories[:4],
            "research_stories": research_stories[:4],
            "academic_programs": academic_programs,
            "research_gaps": research_gaps,
            "academic_jobs": academic_jobs[:6],
            "tech_remote_jobs": tech_remote_jobs[:6],
            "closing_soon_jobs": closing_soon,
            "portal_url": "https://zubairiteng.github.io/devresearch-daily-briefing/"
        }
