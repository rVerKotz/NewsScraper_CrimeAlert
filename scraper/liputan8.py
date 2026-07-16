import re
import logging
from urllib.parse import urljoin

from scraper.base import BaseScraper, Article

logger = logging.getLogger(__name__)


class Liputan8Scraper(BaseScraper):
    BASE_URL = "https://liputan8.id"
    SOURCE_NAME = "liputan8"

    SEARCH_URLS = [
        "/?s=curanmor",
        "/?s=pencurian+motor",
        "/?s=pencurian+sepeda+motor",
    ]

    FALLBACK_CATEGORIES = [
        "/category/hukrim/",
    ]

    def scrape(self) -> list[Article]:
        articles = []
        seen_urls = set()

        for search_path in self.SEARCH_URLS:
            url = urljoin(self.BASE_URL, search_path)
            soup = self._fetch_with_retry(url)
            if not soup:
                continue

            items = (
                soup.select("article")
                or soup.select(".post-card")
                or soup.select(".entry")
                or soup.select(".blog-post")
                or soup.select("div[class*='post']")
                or soup.select("div[class*='article']")
                or soup.select(".box-item")
            )

            for item in items:
                try:
                    link_tag = item.find("a", href=True) if item else None
                    if not link_tag or not link_tag.get("href"):
                        continue

                    href = link_tag["href"]
                    if not href.startswith("http"):
                        href = urljoin(self.BASE_URL, href)

                    if href in seen_urls:
                        continue

                    title_tag = (
                        item.select_one("h2")
                        or item.select_one("h3")
                        or item.select_one(".entry-title")
                        or item.select_one(".post-title")
                    )
                    title = self.clean_text(title_tag.get_text()) if title_tag else ""

                    summary_tag = (
                        item.select_one("p")
                        or item.select_one(".excerpt")
                        or item.select_one(".post-excerpt")
                        or item.select_one(".entry-summary")
                    )
                    summary = self.clean_text(summary_tag.get_text()) if summary_tag else ""

                    img_tag = item.select_one("img")
                    img_url = img_tag.get("src") or img_tag.get("data-src") or "" if img_tag else ""

                    time_tag = item.select_one("time") or item.select_one(".date") or item.select_one(".post-date")
                    published = ""
                    if time_tag:
                        published = time_tag.get("datetime") or self.clean_text(time_tag.get_text())

                    article = Article(
                        title=title,
                        url=href,
                        source=self.SOURCE_NAME,
                        summary=summary,
                        image_url=img_url,
                        published=published,
                    )
                    articles.append(article)
                    seen_urls.add(href)

                except Exception as e:
                    logger.debug("Error parsing article: %s", e)
                    continue

        if not articles:
            articles = self._scrape_fallback(seen_urls)

        return articles

    def _fetch_with_retry(self, url: str):
        """Fetch with retry and alternative headers if blocked."""
        soup = self.fetch(url)
        if soup:
            return soup

        logger.info("Direct fetch failed for %s, trying with curl-compatible headers...", url)
        try:
            alt_headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://www.google.com/",
            }
            resp = self.session.get(url, headers=alt_headers, timeout=15)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            from bs4 import BeautifulSoup
            return BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            logger.warning("Alt headers also failed: %s", e)
            return None

    def _scrape_fallback(self, seen_urls: set) -> list[Article]:
        articles = []
        for cat_path in self.FALLBACK_CATEGORIES:
            url = urljoin(self.BASE_URL, cat_path)
            soup = self._fetch_with_retry(url)
            if not soup:
                continue

            items = (
                soup.select("article")
                or soup.select(".post-card")
                or soup.select(".entry")
                or soup.select("div[class*='post']")
            )

            for item in items:
                try:
                    link_tag = item.find("a", href=True)
                    if not link_tag or not link_tag.get("href"):
                        continue

                    href = link_tag["href"]
                    if not href.startswith("http"):
                        href = urljoin(self.BASE_URL, href)

                    if href in seen_urls:
                        continue

                    title_tag = item.select_one("h2") or item.select_one("h3") or item.select_one(".entry-title")
                    title = self.clean_text(title_tag.get_text()) if title_tag else ""

                    article = Article(
                        title=title,
                        url=href,
                        source=self.SOURCE_NAME,
                    )
                    articles.append(article)
                    seen_urls.add(href)

                except Exception:
                    continue

        return articles

    def scrape_search(self, keyword: str) -> list[Article]:
        articles = self.scrape()
        kw = keyword.lower()
        return [a for a in articles if kw in a.title.lower() or kw in a.summary.lower()]
