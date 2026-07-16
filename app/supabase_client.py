import logging
from typing import Optional

from app.settings_manager import settings
from scraper.base import normalize_article

logger = logging.getLogger(__name__)

_supabase = None


def get_client():
    global _supabase
    if _supabase is not None:
        return _supabase

    if not settings.is_supabase_configured():
        return None

    try:
        from supabase import create_client
        url = settings.get("supabase_url")
        key = settings.get("supabase_service_role_key")
        _supabase = create_client(url, key)
        logger.info("Supabase client initialized")
        return _supabase
    except ImportError:
        logger.error("supabase-py not installed. Run: pip install supabase-py")
        return None
    except Exception as e:
        logger.error("Failed to init Supabase: %s", e)
        return None


def reset_client():
    global _supabase
    _supabase = None


def push_article(article) -> bool:
    normalize_article(article)
    client = get_client()
    if client is None:
        return False

    table = settings.get("supabase_table", "crime_articles")
    try:
        data = {
            "url": article.url,
            "title": article.title,
            "source": article.source,
            "summary": article.summary,
            "content": article.content,
            "published": article.published,
            "image_url": article.image_url,
            "province": article.province,
            "city": article.city,
            "latitude": article.latitude,
            "longitude": article.longitude,
            "crime_type": article.crime_type,
            "relevance_score": article.relevance_score,
            "scraped_at": article.scraped_at,
        }
        client.table(table).insert(data).execute()
        return True
    except Exception as e:
        logger.error("Failed to push article to Supabase: %s", e)
        return False


def push_articles(articles: list) -> dict:
    """Push all articles to Supabase. Returns {succeeded, failed} count."""
    succeeded = 0
    failed = 0

    client = get_client()
    if client is None:
        return {"succeeded": 0, "failed": len(articles), "error": "Supabase not configured"}

    table = settings.get("supabase_table", "crime_articles")
    batch = []
    for article in articles:
        normalize_article(article)
        batch.append({
            "url": article.url,
            "title": article.title,
            "source": article.source,
            "summary": article.summary,
            "content": article.content,
            "published": article.published,
            "image_url": article.image_url,
            "province": article.province,
            "city": article.city,
            "latitude": article.latitude,
            "longitude": article.longitude,
            "crime_type": article.crime_type,
            "relevance_score": article.relevance_score,
            "scraped_at": article.scraped_at,
        })

    try:
        client.table(table).insert(batch).execute()
        succeeded = len(batch)
    except Exception as e:
        logger.error("Supabase batch insert failed, trying individual inserts...")
        for item in batch:
            try:
                client.table(table).insert(item).execute()
                succeeded += 1
            except Exception as e2:
                logger.warning("Failed to push article %s: %s", item.get("url", "?"), e2)
                failed += 1

    return {"succeeded": succeeded, "failed": failed}
