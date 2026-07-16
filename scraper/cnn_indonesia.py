import logging
import re
from datetime import datetime

from bs4 import BeautifulSoup

from scraper.base import BaseScraper, Article
from config import MAX_ARTICLES_PER_SOURCE

logger = logging.getLogger(__name__)


class CNNIndonesiaScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.source = "CNN Indonesia"
        self.tag_urls = [
            "https://www.cnnindonesia.com/tag/curanmor",
            "https://www.cnnindonesia.com/tag/pencurian-motor",
        ]

    def get_articles(self) -> list[Article]:
        articles: list[Article] = []
        seen_urls: set[str] = set()

        for tag_url in self.tag_urls:
            if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                break
            for page_num in range(1, 4):
                if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                    break
                url = tag_url if page_num == 1 else f"{tag_url}/{page_num}"
                logger.info("Fetching CNN Indonesia: %s", url)
                html = self.fetch(url)
                if not html:
                    continue

                soup = BeautifulSoup(html, "html.parser")
                items = soup.select("article, .list, .news-list, .article-item, .feed-item")

                if not items:
                    items = soup.select("a[href*='/nasional/'], a[href*='/news/']")
                    items = [item for item in items if item.get("href") and not item.get("href", "").startswith("#")]
                    items = items[:20]

                for item in items:
                    if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                        break

                    link_tag = item if item.name == "a" and item.get("href") else item.find("a", href=True)
                    if not link_tag:
                        continue
                    article_url = link_tag["href"]
                    if not article_url.startswith("http"):
                        article_url = "https://www.cnnindonesia.com" + article_url

                    if article_url in seen_urls:
                        continue
                    if "/embed/" in article_url or "/video/" in article_url:
                        continue
                    seen_urls.add(article_url)

                    title_tag = item.select_one("h1, h2, h3, h4, .title, .article-title")
                    title = title_tag.get_text(strip=True) if title_tag else link_tag.get("title") or link_tag.get_text(strip=True)

                    summary_tag = item.select_one("p, .summary, .lead, .article-summary, .text-card__content")
                    summary = summary_tag.get_text(strip=True) if summary_tag else ""

                    img_tag = item.select_one("img[src]")
                    image_url = img_tag.get("src") or img_tag.get("data-src") or ""

                    published_tag = item.select_one("time, .date, .article-date, .text-card__date")
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

        logger.info("CNN Indonesia: found %d articles", len(articles))
        return articles

    def scrape_content(self, url: str) -> str:
        html = self.fetch(url)
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.select("script, style, ins, .ads, .share, .comment"):
            tag.decompose()

        contents = (
            soup.select_one("article .detail-text, .detail-text, .content-text")
            or soup.select_one("article .content, .detail-content, .post-content")
            or soup.select_one("article, .article-content, .read__content")
        )
        if contents:
            paragraphs = contents.select("p")
            return "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        return ""

    def scrape_published(self, url: str) -> str:
        html = self.fetch(url)
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.select("script[type='application/ld+json']")
        for script in scripts:
            import json
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

        meta2 = soup.select_one('meta[name="publishdate"]')
        if meta2:
            return self.parse_date(meta2.get("content", ""))

        return ""
