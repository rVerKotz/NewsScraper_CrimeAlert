import logging
import sqlite3
from config import DB_PATH

logger = logging.getLogger(__name__)

_scraped_urls: set[str] = set()


def init_cache():
    global _scraped_urls
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS scraped_urls (
                url TEXT PRIMARY KEY,
                scraped_at TEXT DEFAULT (datetime('now', 'localtime'))
            )"""
        )
        conn.commit()
        rows = conn.execute("SELECT url FROM scraped_urls").fetchall()
        _scraped_urls = {row["url"] for row in rows}
        logger.info("Dedup cache: loaded %d URLs", len(_scraped_urls))
    finally:
        conn.close()


def _ensure_table():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS scraped_urls (
                url TEXT PRIMARY KEY,
                scraped_at TEXT DEFAULT (datetime('now', 'localtime'))
            )"""
        )
        conn.commit()
    finally:
        conn.close()


def is_scraped(url: str) -> bool:
    if not _scraped_urls:
        init_cache()
    return url in _scraped_urls


def mark_scraped(url: str):
    _scraped_urls.add(url)
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute(
            "INSERT OR IGNORE INTO scraped_urls (url) VALUES (?)",
            (url,),
        )
        conn.commit()
    finally:
        conn.close()


def mark_scraped_batch(urls: list[str]):
    _ensure_table()
    _scraped_urls.update(urls)
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.executemany(
            "INSERT OR IGNORE INTO scraped_urls (url) VALUES (?)",
            [(u,) for u in urls],
        )
        conn.commit()
    finally:
        conn.close()


def clear_cache():
    global _scraped_urls
    _scraped_urls.clear()
    _ensure_table()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("DELETE FROM scraped_urls")
        conn.commit()
        logger.info("Dedup cache cleared")
    finally:
        conn.close()
