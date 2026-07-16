import json
import logging

from config import DATA_DIR, MAX_ARTICLES_PER_SOURCE, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "max_articles_per_source": MAX_ARTICLES_PER_SOURCE,
    "request_timeout": REQUEST_TIMEOUT,
    "scrape_interval_minutes": 1440,
    "api_host": "0.0.0.0",
    "api_port": 8000,
}


class Settings:
    def __init__(self):
        self._data: dict = dict(DEFAULT_SETTINGS)
        self._load()

    def _load(self):
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, encoding="utf-8") as f:
                    loaded = json.load(f)
                self._data.update(loaded)
                logger.info("Settings loaded from %s", SETTINGS_FILE)
        except Exception as e:
            logger.warning("Failed to load settings: %s", e)

    def _save(self):
        try:
            DATA_DIR.mkdir(exist_ok=True)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            logger.info("Settings saved to %s", SETTINGS_FILE)
        except Exception as e:
            logger.error("Failed to save settings: %s", e)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def get_all(self) -> dict:
        return dict(self._data)

    def update(self, updates: dict) -> dict:
        changed = {}
        for key, value in updates.items():
            if key in self._data and self._data[key] != value:
                old = self._data[key]
                self._data[key] = value
                changed[key] = {"old": old, "new": value}
        if changed:
            self._save()
        return changed

    def reset(self):
        self._data = dict(DEFAULT_SETTINGS)
        self._save()


settings = Settings()
