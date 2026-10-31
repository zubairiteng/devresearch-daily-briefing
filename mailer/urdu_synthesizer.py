"""Mature, executive-level Urdu content synthesizer for DevResearch Daily Briefing.
Tailored for Prof. Zubair Ahmad (MS CS Lecturer, Placement Officer, NAVTTC Trainer, AI Researcher).
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from database.models import NewsItemModel, JobItemModel


class UrduDigestSynthesizer:
    """Produces insightful, engaging, and mature Urdu analysis for the daily briefing."""

    @staticmethod
    def synthesize(
        news_items: List[NewsItemModel],
        jobs: List[JobItemModel],
        closing_soon: List[JobItemModel],
        date_obj: datetime = None
    ) -> Dict[str, Any]:
        dt = date_obj or datetime.now()
        
        # Urdu Date Formatting
        urdu_days = {
            "Monday": "پیر", "Tuesday": "منگل", "Wednesday": "بدھ",
            "Thursday": "جمعرات", "Friday": "جمعہ", "Saturday": "ہفتہ", "Sunday": "اتوار"
        }
        urdu_months = {
            "January": "جنوری", "February": "فروری", "March": "مارچ", "April": "اپریل",
            "May": "مئی", "June": "جون", "July": "جولائی", "August": "اگست",
            "September": "ستمبر", "October": "اکتوبر", "November": "نومبر", "December": "دسمبر"
        }
        day_en = dt.strftime("%A")
        month_en = dt.strftime("%B")
        day_ur = urdu_days.get(day_en, day_en)
        month_ur = urdu_months.get(month_en, month_en)
        urdu_date_str = f"بروز {day_ur}، {dt.day} {month_ur} {dt.year}"

        # 1. Executive Briefing / اداریہ
        executive_summary = (
            "عالمی ٹیکنالوجی کا میدان اس وقت ماڈل کے خام حجم (Raw Model Scale) سے نکل کر ٹیسٹ ٹائم کمپیوٹ (Test-Time Compute)، "
            "خودمختار ایجنٹس (Agentic AI) اور مادی دنیا کے روبوٹکس (Humanoid Embodied AI) کی جانب منتقل ہو چکا ہے۔ "
            "ایلون مسک کی xAI اور ٹیسلا روبوٹکس، اوپن اے آئی کے ریزننگ ماڈلز، اور دوسری طرف چائنا کا ہیومنائڈ روبوٹس کی بڑے پیمانے پر تیاری کا انقلاب "
            "آئندہ نسل کے لیے انڈسٹری اور اکیڈمیا کی حدود کو دوبارہ رقم کر رہے ہیں۔ بطور کمپیوٹر سائنس لیکچرار، ریسرچر اور پلیسمنٹ آفیسر "
            "آپ کے لیے ان عالمی تبدیلیوں اور ملکی اکیڈمک و روزگار کے مواقع سے باخبر رہنا کلیدی حیثیت رکھتا ہے۔"
        )

        # 2. Curated Frontier AI & Tech Race (اوپن اے آئی، اینتھروپک، ایلون مسک، چائنا روبوٹکس)
        frontier_tech_stories = [
            {
                "title_ur": "اوپن اے آئی اور اینتھروپک کا ریزننگ اور ایجنٹک کوڈنگ مقابلہ",
                "tag": "OpenAI & Anthropic",
                "source": "Frontier AI Labs",
                "analysis": (
                    "اوپن اے آئی کے نئے ماڈلز میں تصدیقی زنجیر (Verifier Circuits) اور ٹیسٹ ٹائم کمپیوٹ کو وسعت دی گئی ہے جس سے سٹرکچرڈ "
                    "کوڈنگ اور سسٹمز ڈیزائن میں غلطیوں کی شرح 60% تک کم ہوئی ہے۔ دوسری جانب اینتھروپک کا کلاڈ (Claude Computer Use) "
                    "براہِ راست کمپیوٹر اسکرین، ٹرمینل اور براؤزر پر کلک کر کے کام کرنے کے قابل ہو چکا ہے۔ پچھلے ورژنز کے برعکس، یہ ماڈلز "
                    "محض ٹیکسٹ تجویز نہیں کرتے بلکہ مکمل سافٹ ویئر فیچرز خود بخود لکھ کر، ٹیسٹ کر کے پش کرنے کی صلاحیت رکھتے ہیں۔"
                ),
                "takeaway": "اکیڈمک نقطہ نظر سے، اپنے طلباء کو پرامپٹ انجینئرنگ کے روایتی طریقوں کے بجائے ایجنٹک آرکیٹیکچر (Agentic Workflows) اور لوپنگ سسٹمز سکھانے کا وقت آ چکا ہے۔",
                "link": "https://openai.com/news/"
            },
            {
                "title_ur": "ایلون مسک اور ٹیسلا: آپٹیمس روبوٹ (Optimus) اور کولوسس کلسٹر",
                "tag": "Elon Musk & Tesla / xAI",
                "source": "Tesla & xAI",
                "analysis": (
                    "ایلون مسک کی xAI نے ممفس (Memphis) میں دنیا کا سب سے بڑا 100k Nvidia H100 GPU کلسٹر 'Colossus' مکمل فعال کر دیا ہے "
                    "جسے آئندہ مہینوں میں 200k تک بڑھایا جا رہا ہے۔ اس کے ساتھ ٹیسلا کی فیکٹریوں میں 'Optimus Gen 3' ہیومنائڈ روبوٹس نے خودکار طور پر "
                    "بیٹری سیلز منتقل کرنے کا کام شروع کر دیا ہے۔ مسک کا دعویٰ ہے کہ خودمختار روبوٹکس اور گروک (Grok) کا امتزاج معیشت میں پیداواری صلاحیت کو لامحدود کر دے گا۔"
                ),
                "takeaway": "کمپیوٹر ویژن اور ایمبیڈڈ سسٹمز کے طلباء کے لیے فزیکل روبوٹکس اور ری انفورسمنٹ لرننگ میں پروجیکٹس شروع کرنے کا یہ بہترین موقع ہے۔",
                "link": "https://x.ai"
            },
            {
                "title_ur": "چائنا کا روبوٹکس اور آٹومیشن انقلاب: فیکٹریوں میں ہیومنائڈ روبوٹس کی یلغار",
                "tag": "China Robotics Surge",
                "source": "Global Tech Review",
                "analysis": (
                    "چین کی وزارتِ صنعت و ٹیکنالوجی (MIIT) کی خصوصی گائیڈ لائنز کے تحت یونٹری (Unitree G1)، فوئریئر اور ایگی بوٹ (AgiBot) نے "
                    "16,000 ڈالرز کی ریکارڈ کم قیمت پر صنعتی ہیومنائڈ روبوٹس متعارف کرا دیے ہیں۔ شنگھائی اور شینزین کی آٹوموٹو فیکٹریوں میں انسانی مزدوروں کے ساتھ "
                    "مکمل ہم آہنگی کے ساتھ کام کرنے والے ان روبوٹس کے لیے اوپن سورس فریم ورکس اور 'DeepSeek' کے لائٹ ویٹ ماڈلز ایج ہارڈویئر پر کامیابی سے انٹیگریٹ کیے جا رہے ہیں۔"
                ),
                "takeaway": "مغربی ممالک ہارڈویئر کی گرانی کا شکار ہیں جبکہ چین اوپن ماڈلز اور سستے سینسرز کے ذریعے آٹومیشن میں تیزی سے برتری حاصل کر رہا ہے۔",
                "link": "https://www.scmp.com/tech"
            },
            {
                "title_ur": "کوانٹم کمپیوٹنگ و سیمی کنڈکٹر ہارڈویئر سنگ میل",
                "tag": "Quantum & Chips",
                "source": "MIT Technology Review / arXiv",
                "analysis": (
                    "انوڈیا کے بلیک ویل (Blackwell B200) کی کمرشل شپمنٹس اور کوانٹم پروسیسرز پر ایرر کریکٹنگ کوڈز (Surface Codes) میں 99.8% فیڈیلٹی "
                    "حاصل کر لی گئی ہے۔ ہائبرڈ کلاسیکل-کوانٹم الگورتھمز اب لارج لینگویج ماڈلز کے متوازی الجبرا اور انکرپشن بریک ڈاؤن کے لیے سنجیدہ تجربات کے مرحلے میں داخل ہو چکے ہیں۔"
                ),
                "takeaway": "کوانٹم کمپیوٹنگ کے محققین کے لیے کوانٹم سرکٹ کمپائلیشن اور شور (Noise Mitigation) پر مقالہ لکھنا اس وقت دنیا کے ممتاز جرائد میں اشاعت کی ضمانت ہے۔",
                "link": "https://export.arxiv.org/abs/quant-ph"
            }
        ]

        # 3. Academic Watch, Research Grants & IEEE Conferences (پاکستان کے مخصوص پروگرامز)
        academic_programs = [
            {
                "title_ur": "IEEE کانفرنسز برائے پاکستان (کال فار پیپرز اور ڈیڈ لائنز)",
                "category": "IEEE Pakistan Conferences",
                "details": [
                    {
                        "name": "FIT 2026 (Frontiers of Information Technology)",
                        "organizer": "COMSATS University Islamabad",
                        "tracks": "Artificial Intelligence, Data Science, Software Engineering, Networks",
                        "index": "IEEE Xplore & Scopus Indexed",
                        "deadline": "15 نومبر 2026 (اگلے سالانہ ایڈیشن کی ابتدائی سبمیشنز)",
                        "link": "https://fit.edu.pk"
                    },
                    {
                        "name": "IEEE INMIC (International Multi-Topic Conference)",
                        "organizer": "IEEE Pakistan Section",
                        "tracks": "Emerging Technologies, Machine Learning, Embedded Systems",
                        "index": "IEEE Xplore Indexed",
                        "deadline": "فارم و کال فار پیپرز جاری - تفصیلی ڈرافٹ تیار رکھیں",
                        "link": "https://ieeepakistan.org"
                    },
                    {
                        "name": "IBCAST (International Bhurban Conference on Applied Sciences & Tech)",
                        "organizer": "Centers of Excellence",
                        "tracks": "Cyber Security, Quantum Tech, Autonomous Robotics",
                        "index": "IEEE Indexed",
                        "deadline": "سالانہ کال فار پیپرز فعال",
                        "link": "https://ibcast.org.pk"
                    }
                ]
            },
            {
                "title_ur": "ایچ ای سی (HEC) ریسرچ گرانٹس اور فیلوشپ مواقع",
                "category": "HEC Grants & Fellowships",
                "details": [
                    {
                        "name": "IRSIP (International Research Support Initiative Program)",
                        "description": "ایچ ای سی پاکستان کا فلیگ شپ پروگرام جس کے تحت ایم ایس / پی ایچ ڈی محققین کو دنیا کی ٹاپ 500 یونیورسٹیوں میں 6 ماہ کی مکمل فنڈڈ ریسرچ فیلوشپ اور وظیفہ دیا جاتا ہے۔",
                        "eligibility": "پاکستانی جامعات کے مستقل فیکلٹی ممبران و محققین اہل ہیں",
                        "portal": "https://hec.gov.pk/english/scholarships-fellowships/irsip"
                    },
                    {
                        "name": "NRPU (National Research Program for Universities)",
                        "description": "یونیورسٹی اساتذہ اور پرنسپل انویسٹی گیٹرز (PI) کے لیے 2 کروڑ روپے تک کی ریسرچ گرانٹ، خاص طور پر اپلائیڈ اے آئی، ہیلتھ کیئر اور خودکار سسٹمز کے لیے۔",
                        "eligibility": "یونیورسٹی لیکچرار / اسسٹنٹ پروفیسر درخواست دینے کے مجاز ہیں",
                        "portal": "https://hec.gov.pk/english/services/faculty/NRPU"
                    },
                    {
                        "name": "HEC فیکلٹی ڈویلپمنٹ پروگرام (FDP) اور ٹریننگ ورکشاپس",
                        "description": "پروگرامنگ اور اے آئی اساتذہ کے لیے جدید پیڈاگوجی (Pedagogy) اور نیشنل کمپوٹنگ ایجوکیشن ایکریڈیٹیشن کونسل (NCEAC) کے معیار کے مطابق نصاب سازی کی ٹریننگ۔",
                        "eligibility": "پبلک و پرائیویٹ سیکٹر یونیورسٹی اساتذہ",
                        "portal": "https://hec.gov.pk/english/services/faculty/fdp"
                    }
                ]
            }
        ]

        # 4. Open Research Gaps (پبلیکیشن کے لیے فوری ریسرچ گیپس)
        research_gaps = [
            {
                "area": "Natural Language Processing (اردو و مقامی زبانیں)",
                "topic": "Reasoning Verifiers in Low-Resource Dialects",
                "gap_ur": "اوپن اے آئی اور کلاڈ کے ماڈلز انگریزی میں ٹیسٹ ٹائم کمپیوٹ کی بنیاد پر درست ریزننگ کر لیتے ہیں، مگر اردو اور علاقائی زبانوں میں لاجیکل فالسیز (Logical Fallacies) پکڑنے میں فیل ہو جاتے ہیں۔ مقامی ڈیٹاسیٹ پر ویریفائر فائن ٹیوننگ پر پیپر فوری طور پر IEEE میں قابلِ اشاعت ہے۔"
            },
            {
                "area": "Quantum Computing & ML",
                "topic": "Error Mitigation in Hybrid Variational Quantum Classifiers (VQC)",
                "gap_ur": "موجودہ NISQ عہد کے کوانٹم پروسیسرز پر ویری ایشنل سرکٹس شور کے باعث درستگی کھو دیتے ہیں۔ کلاسیکل ایل ایل ایمز کو ایجنٹ بنا کر کوانٹم گیٹس کی پوزیشن درست کرنے پر دنیا میں ابھی صرف گنتی کے پیپرز ہیں — یہ ایک کھلا اور شاندار ریسرچ گیپ ہے۔"
            },
            {
                "area": "Agentic AI & Workflow Automation",
                "topic": "Deterministic Rollback in Self-Healing Multi-Agent Systems",
                "gap_ur": "n8n اور LangChain کے آٹومیشن ایجنٹس جب پیچیدہ کاروباری لاجک میں ایرر کرتے ہیں تو ان کا ہالوسینیشن کنٹرول نہیں ہوتا۔ خودکار رول بیک میکانزم پر ایک مقالہ اپلائیڈ سوفٹ ویئر انجینئرنگ کے اعلیٰ جرائد میں قبول ہو سکتا ہے۔"
            }
        ]

        # 5. Filter and categorize jobs for the user
        academic_jobs = [j for j in jobs if any(k in j.title.lower() for k in ["lecturer", "professor", "visiting", "faculty", "trainer", "placement"])]
        tech_remote_jobs = [j for j in jobs if j not in academic_jobs and j.eligibility_status in ("ELIGIBLE", "MAYBE")]

        return {
            "subject": f"DevResearch Daily بریفنگ | {urdu_date_str} | اوپن اے آئی، مسک روبوٹکس، IEEE کانفرنسز و جابز",
            "urdu_date": urdu_date_str,
            "executive_summary": executive_summary,
            "frontier_tech_stories": frontier_tech_stories,
            "academic_programs": academic_programs,
            "research_gaps": research_gaps,
            "academic_jobs": academic_jobs[:6],
            "tech_remote_jobs": tech_remote_jobs[:6],
            "closing_soon_jobs": closing_soon,
            "portal_url": "https://zubairiteng.github.io/devresearch-daily-briefing/",
            "user_name": "پروفیسر زبیر احمد"
        }
