import logging
import re
from datetime import datetime

from bs4 import BeautifulSoup

from scraper.base import BaseScraper, Article
from config import MAX_ARTICLES_PER_SOURCE

logger = logging.getLogger(__name__)


class DetikScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.source = "Detik.com"
        self.tag_urls = [
            "https://www.detik.com/tag/curanmor",
            "https://www.detik.com/tag/pencurian",
            "https://www.detik.com/tag/pencurian-motor",
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
                logger.info("Fetching Detik: %s", url)
                html = self.fetch(url)
                if not html:
                    continue

                soup = BeautifulSoup(html, "html.parser")
                items = soup.select("article, .list-berita, .media, .list-news, .feed-artikel")

                if not items:
                    items = soup.select("a[href*='detik.com/']")
                    items = [a for a in items if a.get("href") and self._is_article_url(a["href"])]
                    items = items[:30]

                for item in items:
                    if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                        break

                    link_tag = item if item.name == "a" and item.get("href") else item.find("a", href=True)
                    if not link_tag:
                        continue

                    article_url = link_tag["href"]
                    if not article_url.startswith("http"):
                        article_url = "https:" + article_url if article_url.startswith("//") else "https://www.detik.com" + article_url

                    if article_url in seen_urls:
                        continue
                    seen_urls.add(article_url)

                    title_tag = item.select_one("h1, h2, h3, .title, .media__title, .entry-title")
                    title = title_tag.get_text(strip=True) if title_tag else link_tag.get("title") or link_tag.get_text(strip=True)

                    summary_tag = item.select_one("p, .summary, .lead, .media__desc")
                    summary = summary_tag.get_text(strip=True) if summary_tag else ""

                    img_tag = item.select_one("img[src]")
                    image_url = ""
                    if img_tag:
                        image_url = (img_tag.get("data-src") or img_tag.get("src") or
                                     img_tag.get("data-lazy-src") or img_tag.get("data-original") or "")

                    published_tag = item.select_one("time, .date, .media__date")
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

        logger.info("Detik: found %d articles", len(articles))
        return articles

    def _is_article_url(self, url: str) -> bool:
        patterns = [
            r"detik\.com/([a-z-]+)/berita-\d+",
            r"detik\.com/([a-z-]+)/d-\d+",
            r"news\.detik\.com/berita-\d+",
            r"news\.detik\.com/[a-z-]+-\d+",
            r"[a-z-]+\.detik\.com/[a-z-]+-\d+",
        ]
        return any(re.search(p, url) for p in patterns)

    def scrape_content(self, url: str) -> str:
        html = self.fetch(url)
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.select("script, style, ins, .ads, .share"):
            tag.decompose()

        contents = (
            soup.select_one("article .detail__body-text, .detail__body, .detail__wrap")
            or soup.select_one("article .content, .read__content, .itp_body, .detail-text")
            or soup.select_one("article, .detail-content, .article-body, main")
            or soup.select_one(".entry-content, .content-body, .article-detail, #content")
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

        date_div = soup.select_one(".detail__date, .date, .entry-date, time")
        if date_div:
            text = date_div.get_text(strip=True)
            parsed = self.parse_date(text)
            if parsed:
                return parsed

        return ""
