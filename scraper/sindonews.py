import logging
import json
import re
from datetime import datetime

from bs4 import BeautifulSoup

from scraper.base import BaseScraper, Article
from config import MAX_ARTICLES_PER_SOURCE

logger = logging.getLogger(__name__)


class SindonewsScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.source = "Sindonews"
        self.base_url = "https://www.sindonews.com"
        self.topic_urls = [
            "https://www.sindonews.com/topic/1640/curanmor",
            "https://www.sindonews.com/topic/9175/maling-motor",
            "https://www.sindonews.com/topic/4361/sindikat-curanmor",
            "https://www.sindonews.com/topic/1362/pencurian-motor",
        ]
        self.search_urls = [
            "https://www.sindonews.com/search/gokanal?type=artikel&q=curanmor&pid=7",
            "https://www.sindonews.com/search/gokanal?type=artikel&q=curanmor&pid=5",
        ]

    def get_articles(self) -> list[Article]:
        articles: list[Article] = []
        seen_urls: set[str] = set()

        for topic_url in self.topic_urls:
            if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                break
            logger.info("Fetching Sindonews topic: %s", topic_url)
            html = self.fetch(topic_url)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            self._extract_from_listing(soup, articles, seen_urls)

        for search_url in self.search_urls:
            if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                break
            logger.info("Fetching Sindonews search: %s", search_url)
            html = self.fetch(search_url)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            self._extract_from_listing(soup, articles, seen_urls)

        logger.info("Sindonews: found %d articles", len(articles))
        return articles

    def _extract_from_listing(self, soup: BeautifulSoup, articles: list, seen_urls: set):
        items = soup.select("div.warp-article, article, .list-news, .article-item, .news-item")
        if not items:
            items = soup.select("a[href*='sindonews.com/read'], a[href*='sindonews.com/fokus']")
            items = [a for a in items if a.get("href") and "sindonews.com" in a["href"]]
            items = list(dict.fromkeys(items))[:30]

        for item in items:
            if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                break

            link_tag = item if item.name == "a" and item.get("href") else item.find("a", href=True)
            if not link_tag:
                continue

            article_url = link_tag["href"]
            if not article_url.startswith("http"):
                article_url = "https://www.sindonews.com" + article_url

            if article_url in seen_urls:
                continue
            if "sindonews.com/topic/" in article_url:
                continue
            seen_urls.add(article_url)

            title_tag = item.select_one(
                "div.title-article a, h1 a, h2 a, h3 a, h4 a, "
                ".title a, .news-title a, .article-title a, .post-title a, "
                ".title-article, .news-title"
            )
            if title_tag:
                title = title_tag.get_text(strip=True)
            else:
                title = link_tag.get("title") or link_tag.get_text(strip=True)

            summary_tag = item.select_one("p, .summary, .lead, .news-summary, .post-summary, .article-summary")
            summary = summary_tag.get_text(strip=True) if summary_tag else ""

            img_tag = item.select_one("img[src]")
            image_url = ""
            if img_tag:
                image_url = img_tag.get("src") or img_tag.get("data-src") or ""

            published_tag = item.select_one("time, .date, .news-date, .post-date, .article-date")
            published = published_tag.get_text(strip=True) if published_tag else ""

            article_obj = Article(
                url=article_url,
                title=title[:500],
                source=self.source,
                summary=summary[:500],
                published=self.parse_date(published),
                image_url=image_url,
                scraped_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            content = self.scrape_content(article_url)
            if content:
                article_obj.content = content

            published_detail = self.scrape_published(article_url)
            if published_detail:
                article_obj.published = published_detail

            articles.append(article_obj)

    def scrape_content(self, url: str) -> str:
        html = self.fetch(url)
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.select("script, style, ins, .ads, .share"):
            tag.decompose()

        contents = (
            soup.select_one(".detail-desc")
            or soup.select_one("article .detail-text, .detail-text, .content-text")
            or soup.select_one("article .content, .detail-content, .post-content")
            or soup.select_one("article, .article-body, .read-content")
        )
        if contents:
            text = contents.get_text(separator="\n", strip=True)
            return text
        return ""

    def scrape_published(self, url: str) -> str:
        html = self.fetch(url)
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.select("script[type='application/ld+json']")
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    date_pub = data.get("datePublished") or data.get("dateCreated") or ""
                    if date_pub:
                        return self.parse_date(date_pub)
            except (json.JSONDecodeError, AttributeError):
                continue

        time_tags = soup.select("time[datetime]")
        for t in time_tags:
            dt = t.get("datetime")
            if dt:
                return self.parse_date(dt)

        meta = soup.select_one('meta[property="article:published_time"]')
        if meta:
            return self.parse_date(meta.get("content", ""))

        date_div = soup.select_one(".detail-date-artikel, .detail-date, .date, .article-date, time")
        if date_div:
            text = date_div.get_text(strip=True)
            parsed = self.parse_date(text)
            if parsed:
                return parsed

        return ""
