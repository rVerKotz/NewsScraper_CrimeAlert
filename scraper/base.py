import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import requests

from config import USER_AGENT, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


@dataclass
class Article:
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

    def __post_init__(self):
        if not self.scraped_at:
            self.scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class BaseScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self.timeout = REQUEST_TIMEOUT

    def fetch(self, url: str, **kwargs) -> Optional[str]:
        try:
            resp = self.session.get(url, timeout=self.timeout, **kwargs)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        except requests.RequestException as e:
            logger.warning("Failed to fetch %s: %s", url, e)
            return None

    def fetch_json(self, url: str, **kwargs) -> Optional[dict]:
        try:
            resp = self.session.get(url, timeout=self.timeout, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning("Failed to fetch JSON from %s: %s", url, e)
            return None

    def parse_date(self, date_str: str) -> str:
        if not date_str:
            return ""
        date_str = date_str.strip()
        for fmt in [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d %B %Y %H:%M",
            "%B %d, %Y %H:%M",
            "%d %B %Y - %H:%M",
            "%d/%m/%Y %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d",
            "%d %B %Y",
            "%B %d, %Y",
        ]:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        return date_str

    def get_articles(self) -> list[Article]:
        raise NotImplementedError

    def scrape_content(self, url: str) -> str:
        raise NotImplementedError

    def scrape_published(self, url: str) -> str:
        raise NotImplementedError

    def scrape(self) -> list[Article]:
        articles = self.get_articles()
        for article in articles:
            if not article.published:
                published = self.scrape_published(article.url)
                if published:
                    article.published = published
            if not article.content:
                content = self.scrape_content(article.url)
                if content:
                    article.content = content
        return articles
