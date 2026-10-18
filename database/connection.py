"""SQLite database connection and schema initialization with WAL mode."""
import sqlite3
from pathlib import Path
from typing import Generator
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "devresearch.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for high concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def db_session() -> Generator[sqlite3.Connection, None, None]:
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize database tables, indexes, and initial constraints."""
    with db_session() as conn:
        cursor = conn.cursor()

        # News & Research Items
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                source_name TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL,
                why_it_matters TEXT,
                research_gap TEXT,
                published_at TEXT,
                fetched_at TEXT NOT NULL,
                score INTEGER DEFAULT 50,
                read_later BOOLEAN DEFAULT 0,
                metadata_json TEXT
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_category ON news_items(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_fetched ON news_items(fetched_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_read_later ON news_items(read_later);")

        # Jobs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                organization TEXT NOT NULL,
                city TEXT NOT NULL,
                job_type TEXT DEFAULT 'Full-Time',
                required_qualification TEXT,
                required_experience TEXT,
                age_limit TEXT,
                salary TEXT,
                deadline TEXT,
                apply_link TEXT,
                source_links TEXT NOT NULL, -- JSON array of source URLs
                primary_url TEXT NOT NULL UNIQUE,
                eligibility_status TEXT NOT NULL, -- 'ELIGIBLE', 'MAYBE', 'NOT ELIGIBLE'
                eligibility_reason TEXT NOT NULL,
                relevance_score INTEGER DEFAULT 50,
                application_stage TEXT DEFAULT 'Saved', -- 'Saved', 'Applied', 'Interview', 'Rejected', 'Offer'
                notes TEXT DEFAULT '',
                application_date TEXT,
                fetched_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_city ON jobs(city);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_eligibility ON jobs(eligibility_status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_stage ON jobs(application_stage);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at);")

        # Research Gaps Dedicated Board
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id INTEGER,
                title TEXT NOT NULL,
                topic TEXT NOT NULL,
                gap_description TEXT NOT NULL,
                tags TEXT, -- JSON array or comma separated
                status TEXT DEFAULT 'open', -- 'open', 'investigating', 'published'
                created_at TEXT NOT NULL,
                FOREIGN KEY (news_id) REFERENCES news_items(id) ON DELETE SET NULL
            );
        """)

        # Daily Digest Run Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS digest_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_time TEXT NOT NULL,
                status TEXT NOT NULL, -- 'success', 'failed'
                news_count INTEGER DEFAULT 0,
                jobs_count INTEGER DEFAULT 0,
                subject TEXT,
                recipient_list TEXT,
                error_message TEXT
            );
        """)
