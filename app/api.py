import asyncio
import csv
import io
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.dedup_cache import init_cache, is_scraped, mark_scraped_batch, clear_cache
from app.settings_manager import settings
from config import CITY_COORDS
from scraper import get_all_scrapers
from scraper.base import Article, normalize_article
from analyzer.crime_detector import analyze_article

logger = logging.getLogger(__name__)

_scrape_lock = asyncio.Lock()


# ── Pydantic schemas ──────────────────────────────────────────

class SettingsOut(BaseModel):
    max_articles_per_source: int
    request_timeout: int
    scrape_interval_minutes: int
    api_host: str
    api_port: int


class SettingsUpdate(BaseModel):
    max_articles_per_source: Optional[int] = None
    request_timeout: Optional[int] = None
    scrape_interval_minutes: Optional[int] = None
    api_host: Optional[str] = None
    api_port: Optional[int] = None


class ArticleOut(BaseModel):
    url: str
    title: str
    source: str
    summary: str = ""
    content: str = ""
    published: str = ""
    image_url: str = ""
    province: str = ""
    city: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    crime_type: str = ""
    relevance_score: float = 0.0
    scraped_at: str = ""


# ── App ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_cache()
    logger.info("CrimeAlert API started (stateless mode)")
    yield


app = FastAPI(
    title="CrimeAlert API",
    description="Stateless news scraper & crime analyzer for Indonesian news",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Settings endpoints ────────────────────────────────────────

@app.get("/api/settings", response_model=SettingsOut)
def get_settings():
    return SettingsOut(**settings.get_all())


@app.put("/api/settings", response_model=dict)
def update_settings(body: SettingsUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    changed = settings.update(updates)
    if not changed:
        return {"status": "no_changes"}
    return {"status": "updated", "changes": {k: v for k, v in changed.items()}}


@app.post("/api/settings/reset")
def reset_settings():
    settings.reset()
    return {"status": "reset", "settings": settings.get_all()}


# ── Info endpoints ────────────────────────────────────────────

@app.get("/api/sources", response_model=list[str])
def list_sources():
    return list(get_all_scrapers().keys())


@app.get("/api/cities", response_model=dict)
def list_cities(q: str = Query("", max_length=50)):
    query = q.lower().strip()
    results = {}
    for name, (prov, lat, lon) in CITY_COORDS.items():
        if not query or query in name:
            results[name] = {"province": prov, "latitude": lat, "longitude": lon}
    return results


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "stateless"}


# ── Cache endpoints ────────────────────────────────────────────

@app.delete("/api/cache/clear")
def cache_clear():
    clear_cache()
    return {"status": "cache_cleared"}


# ── Scrape endpoint ───────────────────────────────────────────

def _articles_to_csv(articles: list[Article]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "url", "title", "source", "summary", "content", "published",
        "image_url", "province", "city", "latitude", "longitude",
        "crime_type", "relevance_score", "scraped_at",
    ])
    for a in articles:
        writer.writerow([
            a.url, a.title, a.source, a.summary, a.content, a.published,
            a.image_url, a.province, a.city, a.latitude, a.longitude,
            a.crime_type, a.relevance_score, a.scraped_at,
        ])
    return output.getvalue()


@app.post("/api/scrape")
async def trigger_scrape(format: str = Query("json", pattern="^(json|csv)$")):
    async with _scrape_lock:
        loop = asyncio.get_event_loop()
        all_articles: list[Article] = []

        scrapers = get_all_scrapers()
        enabled = settings.get("enabled_sources", list(scrapers.keys()))

        for name, scraper in scrapers.items():
            if name not in enabled:
                continue
            try:
                articles = await loop.run_in_executor(None, scraper.scrape)
                for art in articles:
                    analyze_article(art)

                current_articles = []
                for art in articles:
                    normalize_article(art)
                    if not is_scraped(art.url):
                        current_articles.append(art)

                if not current_articles and articles:
                    current_articles = articles

                if current_articles:
                    mark_scraped_batch([a.url for a in current_articles])
                all_articles.extend(articles)

                logger.info("%s: %d articles (%d new)", name, len(articles), len(current_articles))
            except Exception as e:
                logger.exception("Scrape error for %s: %s", name, e)

        if format == "csv":
            csv_content = _articles_to_csv(all_articles)
            return PlainTextResponse(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=scraped_articles.csv"},
            )

        normalized_articles = [normalize_article(a) for a in all_articles]
        return [ArticleOut(**{
            "url": a.url,
            "title": a.title,
            "source": a.source,
            "summary": a.summary,
            "content": a.content,
            "published": a.published,
            "image_url": a.image_url,
            "province": a.province,
            "city": a.city,
            "latitude": a.latitude,
            "longitude": a.longitude,
            "crime_type": a.crime_type,
            "relevance_score": a.relevance_score,
            "scraped_at": a.scraped_at,
        }) for a in normalized_articles]
