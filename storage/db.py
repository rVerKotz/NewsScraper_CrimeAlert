import sqlite3
import logging
from datetime import datetime
from typing import Optional

from config import DB_PATH

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                summary TEXT DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                published TEXT DEFAULT '',
                image_url TEXT NOT NULL DEFAULT '',
                province TEXT NOT NULL DEFAULT '',
                city TEXT NOT NULL DEFAULT '',
                latitude REAL NOT NULL DEFAULT 0.0,
                longitude REAL NOT NULL DEFAULT 0.0,
                crime_type TEXT DEFAULT '',
                relevance_score REAL DEFAULT 0.0,
                is_read INTEGER DEFAULT 0,
                is_warning_sent INTEGER DEFAULT 0,
                scraped_at TEXT NOT NULL DEFAULT '',
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
            CREATE INDEX IF NOT EXISTS idx_articles_city ON articles(city);
            CREATE INDEX IF NOT EXISTS idx_articles_province ON articles(province);
            CREATE INDEX IF NOT EXISTS idx_articles_crime_type ON articles(crime_type);
            CREATE INDEX IF NOT EXISTS idx_articles_relevance ON articles(relevance_score DESC);
            CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published);
            CREATE INDEX IF NOT EXISTS idx_articles_created ON articles(created_at DESC);

            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT DEFAULT '',
                province TEXT DEFAULT '',
                crime_type TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                warning_type TEXT DEFAULT 'headline',
                message TEXT DEFAULT '',
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (article_id) REFERENCES articles(id)
            );
        """)
        conn.commit()
        logger.info("Database initialized at %s", DB_PATH)
    finally:
        conn.close()


def save_article(article) -> Optional[int]:
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO articles
               (url, title, source, summary, content, published, image_url,
                province, city, latitude, longitude, crime_type, relevance_score, scraped_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                article.url,
                article.title,
                article.source,
                article.summary,
                article.content,
                article.published or "",
                article.image_url,
                article.province,
                article.city,
                article.latitude,
                article.longitude,
                article.crime_type,
                article.relevance_score,
                article.scraped_at,
            ),
        )
        conn.commit()
        if cursor.lastrowid:
            return cursor.lastrowid

        row = conn.execute("SELECT id FROM articles WHERE url = ?", (article.url,)).fetchone()
        return row["id"] if row else None
    except Exception as e:
        logger.error("Error saving article: %s", e)
        return None
    finally:
        conn.close()


def article_exists(url: str) -> bool:
    conn = get_connection()
    try:
        row = conn.execute("SELECT 1 FROM articles WHERE url = ?", (url,)).fetchone()
        return row is not None
    finally:
        conn.close()


def get_crime_articles(
    source: str = "",
    city: str = "",
    province: str = "",
    crime_type: str = "",
    limit: int = 50,
    offset: int = 0,
    min_score: float = 0.0,
) -> list[dict]:
    conn = get_connection()
    try:
        conditions = ["relevance_score > ?"]
        params: list = [min_score]

        if source:
            conditions.append("source = ?")
            params.append(source)
        if city:
            conditions.append("city LIKE ?")
            params.append(f"%{city}%")
        if province:
            conditions.append("province LIKE ?")
            params.append(f"%{province}%")
        if crime_type:
            conditions.append("crime_type = ?")
            params.append(crime_type)

        where = " AND ".join(conditions)
        rows = conn.execute(
            f"SELECT * FROM articles WHERE {where} ORDER BY relevance_score DESC, published DESC, created_at DESC LIMIT ? OFFSET ?",
            (*params, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_latest_articles(limit: int = 20) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM articles ORDER BY published DESC, created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_unread_count() -> int:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM articles WHERE is_read = 0 AND relevance_score > 0"
        ).fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


def get_stats() -> dict:
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) as c FROM articles").fetchone()["c"]
        crime = conn.execute("SELECT COUNT(*) as c FROM articles WHERE relevance_score > 0").fetchone()["c"]
        unread = conn.execute("SELECT COUNT(*) as c FROM articles WHERE is_read = 0 AND relevance_score > 0").fetchone()["c"]

        top_cities = conn.execute(
            "SELECT city, COUNT(*) as cnt FROM articles WHERE city != '' AND relevance_score > 0 GROUP BY city ORDER BY cnt DESC LIMIT 10"
        ).fetchall()

        top_provinces = conn.execute(
            "SELECT province, COUNT(*) as cnt FROM articles WHERE province != '' AND relevance_score > 0 GROUP BY province ORDER BY cnt DESC LIMIT 10"
        ).fetchall()

        top_crimes = conn.execute(
            "SELECT crime_type, COUNT(*) as cnt FROM articles WHERE crime_type != '' GROUP BY crime_type ORDER BY cnt DESC LIMIT 10"
        ).fetchall()

        by_source = conn.execute(
            "SELECT source, COUNT(*) as cnt FROM articles GROUP BY source ORDER BY cnt DESC"
        ).fetchall()

        return {
            "total": total,
            "crime_articles": crime,
            "unread": unread,
            "top_cities": [dict(r) for r in top_cities],
            "top_provinces": [dict(r) for r in top_provinces],
            "top_crimes": [dict(r) for r in top_crimes],
            "by_source": [dict(r) for r in by_source],
        }
    finally:
        conn.close()


def mark_as_read(article_id: int):
    conn = get_connection()
    try:
        conn.execute("UPDATE articles SET is_read = 1 WHERE id = ?", (article_id,))
        conn.commit()
    finally:
        conn.close()


def add_user_preference(city: str = "", province: str = "", crime_type: str = ""):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO user_preferences (city, province, crime_type) VALUES (?, ?, ?)",
            (city.lower(), province.lower(), crime_type.lower()),
        )
        conn.commit()
    finally:
        conn.close()


def get_user_preferences() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM user_preferences WHERE is_active = 1 ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def remove_user_preference(pref_id: int):
    conn = get_connection()
    try:
        conn.execute("UPDATE user_preferences SET is_active = 0 WHERE id = ?", (pref_id,))
        conn.commit()
    finally:
        conn.close()


def save_warning(article_id: int, message: str, warning_type: str = "headline") -> Optional[int]:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO warnings (article_id, warning_type, message) VALUES (?, ?, ?)",
            (article_id, warning_type, message),
        )
        conn.execute("UPDATE articles SET is_warning_sent = 1 WHERE id = ?", (article_id,))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        logger.error("Error saving warning: %s", e)
        return None
    finally:
        conn.close()


def get_warnings(limit: int = 20) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT w.*, a.title, a.url, a.source, a.city, a.province,
                      a.latitude, a.longitude, a.crime_type, a.relevance_score,
                      a.published
               FROM warnings w
               JOIN articles a ON w.article_id = a.id
               ORDER BY w.created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
