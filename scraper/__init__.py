from scraper.cnn_indonesia import CNNIndonesiaScraper
from scraper.detik import DetikScraper
from scraper.sindonews import SindonewsScraper

SCRAPERS = {
    "cnnindonesia": CNNIndonesiaScraper,
    "detik": DetikScraper,
    "sindonews": SindonewsScraper,
}

def get_scraper(name: str):
    cls = SCRAPERS.get(name.lower())
    if cls is None:
        raise ValueError(f"Unknown scraper: {name}. Available: {list(SCRAPERS.keys())}")
    return cls()

def get_all_scrapers():
    return {name: cls() for name, cls in SCRAPERS.items()}
