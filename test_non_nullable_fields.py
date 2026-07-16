import asyncio
from unittest.mock import patch

from analyzer.crime_detector import analyze_article
from app.api import trigger_scrape
from scraper.base import Article
from storage.db import init_db, save_article


def test_article_defaults_are_filled_before_save():
    init_db()

    article = Article(
        url="https://example.com/test",
        title="Test title",
        source="Test source",
        summary="",
        content="",
        image_url="",
        province="",
        city="",
        latitude=0.0,
        longitude=0.0,
        scraped_at="",
    )

    analyze_article(article)

    saved_id = save_article(article)
    assert saved_id is not None
    assert article.content != ""
    assert article.image_url != ""
    assert article.province != ""
    assert article.city != ""
    assert article.latitude is not None
    assert article.longitude is not None
    assert article.scraped_at != ""


def test_scrape_endpoint_returns_current_articles_even_when_cached():
    class StubScraper:
        def scrape(self):
            return [
                Article(
                    url="https://example.com/article-1",
                    title="Stub title",
                    source="Stub source",
                    summary="Stub summary",
                    content="Stub content",
                    image_url="https://example.com/image.jpg",
                    province="Jakarta",
                    city="Jakarta",
                    latitude=-6.2,
                    longitude=106.8,
                    scraped_at="2026-01-01 00:00:00",
                )
            ]

    async def run_test():
        with patch("app.api.get_all_scrapers", return_value={"stub": StubScraper()}), \
             patch("app.api.is_scraped", return_value=True), \
             patch("app.api.mark_scraped_batch") as mark_mock:
            result = await trigger_scrape(format="json")
            assert len(result) == 1
            assert result[0].url == "https://example.com/article-1"
            mark_mock.assert_called_once()

    asyncio.run(run_test())


if __name__ == "__main__":
    test_article_defaults_are_filled_before_save()
    test_scrape_endpoint_returns_current_articles_even_when_cached()
