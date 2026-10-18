"""Database repository for news items and research gaps."""
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from database.connection import db_session
from database.models import NewsItemModel, ResearchGapModel
from summarizer.base import SummaryResult
from fetchers.base import RawItem


class NewsRepository:
    @staticmethod
    def save_news_item(item: RawItem, summary: SummaryResult, score: int, category: str) -> Optional[int]:
        now_str = datetime.now(timezone.utc).isoformat()
        pub_str = item.published_at.isoformat() if item.published_at else now_str

        with db_session() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO news_items (
                        title, url, source_name, category, summary, why_it_matters,
                        research_gap, published_at, fetched_at, score, read_later, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    ON CONFLICT(url) DO UPDATE SET
                        summary=excluded.summary,
                        why_it_matters=excluded.why_it_matters,
                        research_gap=excluded.research_gap,
                        score=excluded.score
                """, (
                    summary.headline or item.title,
                    item.url,
                    item.source_name,
                    category,
                    summary.summary_text,
                    summary.why_it_matters,
                    summary.research_gap,
                    pub_str,
                    now_str,
                    score,
                    json.dumps(item.extra)
                ))
                news_id = cursor.lastrowid

                # If research gap exists, save to research_gaps table
                if summary.research_gap:
                    cursor.execute("""
                        INSERT INTO research_gaps (news_id, title, topic, gap_description, tags, status, created_at)
                        VALUES (?, ?, ?, ?, ?, 'open', ?)
                    """, (
                        news_id,
                        summary.headline,
                        item.extra.get("research_topic", "General Research"),
                        summary.research_gap,
                        json.dumps([category, item.source_name]),
                        now_str
                    ))

                return news_id
            except Exception as e:
                # URL might already exist if conflict handler wasn't hit or db locked
                return None

    @staticmethod
    def get_latest_news(limit: int = 25, category: Optional[str] = None) -> List[NewsItemModel]:
        with db_session() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute("""
                    SELECT * FROM news_items WHERE category = ? ORDER BY id DESC LIMIT ?
                """, (category, limit))
            else:
                cursor.execute("""
                    SELECT * FROM news_items ORDER BY id DESC LIMIT ?
                """, (limit,))
            rows = cursor.fetchall()
            return [NewsRepository._row_to_model(r) for r in rows]

    @staticmethod
    def get_history(
        query: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        only_read_later: bool = False,
        limit: int = 100
    ) -> List[NewsItemModel]:
        with db_session() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM news_items WHERE 1=1"
            params: List[Any] = []

            if only_read_later:
                sql += " AND read_later = 1"
            if category and category != "all":
                sql += " AND category = ?"
                params.append(category)
            if source and source != "all":
                sql += " AND source_name LIKE ?"
                params.append(f"%{source}%")
            if query:
                sql += " AND (title LIKE ? OR summary LIKE ? OR why_it_matters LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])

            sql += " ORDER BY id DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [NewsRepository._row_to_model(r) for r in rows]

    @staticmethod
    def toggle_read_later(item_id: int) -> bool:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT read_later FROM news_items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if not row:
                return False
            new_val = 0 if row["read_later"] else 1
            cursor.execute("UPDATE news_items SET read_later = ? WHERE id = ?", (new_val, item_id))
            return bool(new_val)

    @staticmethod
    def get_research_gaps() -> List[ResearchGapModel]:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM research_gaps ORDER BY id DESC")
            rows = cursor.fetchall()
            results = []
            for r in rows:
                tags = json.loads(r["tags"]) if r["tags"] else []
                results.append(ResearchGapModel(
                    id=r["id"],
                    news_id=r["news_id"],
                    title=r["title"],
                    topic=r["topic"],
                    gap_description=r["gap_description"],
                    tags=tags,
                    status=r["status"],
                    created_at=r["created_at"]
                ))
            return results

    @staticmethod
    def _row_to_model(r) -> NewsItemModel:
        meta = json.loads(r["metadata_json"]) if r["metadata_json"] else {}
        return NewsItemModel(
            id=r["id"],
            title=r["title"],
            url=r["url"],
            source_name=r["source_name"],
            category=r["category"],
            summary=r["summary"],
            why_it_matters=r["why_it_matters"],
            research_gap=r["research_gap"],
            published_at=r["published_at"],
            fetched_at=r["fetched_at"],
            score=r["score"],
            read_later=bool(r["read_later"]),
            metadata=meta
        )
