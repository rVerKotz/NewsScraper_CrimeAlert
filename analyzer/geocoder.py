import json
import logging
import re

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from config import DATA_DIR

logger = logging.getLogger(__name__)

GEOCODE_CACHE_FILE = DATA_DIR / "geocode_cache.json"

_geolocator = Nominatim(user_agent="NewsScraperCrimeAlert/1.0", timeout=15)
_geocode = RateLimiter(_geolocator.geocode, min_delay_seconds=1.0)

_SKIP_WORDS = frozenset({
    "sana", "sini", "situ", "mana", "rumah", "tempat", "lokasi",
    "dalam", "atas", "bawah", "depan", "belakang", "samping",
    "sekitar", "dekat", "antara", "dengan", "telah", "tidak",
    "polisi", "warga", "pelaku", "korban", "tersangka",
    "indonesia",
})


def _load_cache() -> dict:
    if GEOCODE_CACHE_FILE.exists():
        try:
            with open(GEOCODE_CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load geocode cache: %s", e)
    return {}


def _save_cache(cache: dict) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(GEOCODE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning("Failed to save geocode cache: %s", e)


def geocode_location(name: str) -> tuple[str, str, float, float]:
    key = name.strip().lower()
    cache = _load_cache()
    if key in cache:
        entry = cache[key]
        return entry["city"], entry["province"], entry["lat"], entry["lon"]

    result = _geopy_lookup(name)

    cache[key] = {
        "city": result[0],
        "province": result[1],
        "lat": result[2],
        "lon": result[3],
    }
    _save_cache(cache)
    return result


_PROVINCE_KNOWN = frozenset({
    "aceh", "bali", "banten", "bengkulu", "gorontalo", "jakarta", "jambi",
    "jawa barat", "jawa tengah", "jawa timur", "kalimantan barat",
    "kalimantan selatan", "kalimantan tengah", "kalimantan timur",
    "kalimantan utara", "kepulauan bangka belitung", "kepulauan riau",
    "lampung", "maluku", "maluku utara", "nusa tenggara barat",
    "nusa tenggara timur", "papua", "papua barat", "papua barat daya",
    "papua pegunungan", "papua selatan", "papua tengah", "riau",
    "sulawesi barat", "sulawesi selatan", "sulawesi tengah",
    "sulawesi tenggara", "sulawesi utara", "sumatera barat",
    "sumatera selatan", "sumatera utara", "di yogyakarta",
    "dki jakarta", "daerah istimewa yogyakarta",
})

_COUNTRIES = frozenset({
    "indonesia", "united states", "france", "malaysia", "singapore",
    "thailand", "australia", "japan", "china", "india", "united kingdom",
    "germany", "netherlands", "belgium", "switzerland", "italy", "spain",
    "portugal", "russia", "canada", "brazil", "mexico", "argentina",
    "egypt", "south africa", "nigeria", "kenya", "saudi arabia",
    "united arab emirates", "qatar", "turkey", "south korea",
    "netherlands", "sweden", "norway", "denmark", "finland", "poland",
})


def _parse_province(display_name: str) -> str:
    parts = [p.strip() for p in display_name.split(",")]
    parts = [p for p in parts if p and not p.replace(" ", "").replace("-", "").isdigit()]

    for part in parts:
        if part.lower() in _PROVINCE_KNOWN:
            return part

    if len(parts) >= 3:
        for part in parts[1:-1]:
            if part.lower() not in _COUNTRIES:
                return part

    return ""


def _geopy_lookup(location_name: str) -> tuple[str, str, float, float]:
    queries = [
        (location_name, None),
        (location_name, "Indonesia"),
    ]

    for q, country in queries:
        try:
            if country:
                location = _geocode(q, country_codes="id")
            else:
                location = _geocode(q)

            if location is None:
                continue

            lat = location.latitude
            lon = location.longitude
            raw = location.raw or {}
            address = raw.get("address", {})

            province = (
                address.get("state")
                or address.get("region")
                or _parse_province(location.address or "")
            )

            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("county")
                or location_name
            )

            return city, province, lat, lon

        except Exception as e:
            logger.warning("Geopy lookup error for %s: %s", location_name, e)

    return "", "", 0.0, 0.0


_ADMIN_PREFIXES = [
    "kabupaten", "kecamatan", "kelurahan", "desa", "dusun",
]

_ADMIN_PREFIX_PATTERN = r"(?:" + "|".join(r"(?i:" + p + r")\s+" for p in _ADMIN_PREFIXES) + r")?"

_DI_REGEX = re.compile(
    r"\bdi\s+" + _ADMIN_PREFIX_PATTERN +
    r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)"
)

_KABUPATEN_REGEX = re.compile(
    r"(?i:\bkabupaten\s+)([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)"
)


def extract_candidate_locations(text: str) -> list[tuple[str, bool]]:
    candidates: list[tuple[str, bool]] = []
    seen = set()

    for m in _KABUPATEN_REGEX.finditer(text):
        name = m.group(1).strip()
        low = name.lower()
        if low not in seen and low not in _SKIP_WORDS:
            seen.add(low)
            candidates.append((name, True))

    for m in _DI_REGEX.finditer(text):
        name = m.group(1).strip()
        low = name.lower()
        if low not in seen and low not in _SKIP_WORDS:
            is_regency = bool(re.search(r"(?i)\bkabupaten\b", m.group(0)))
            seen.add(low)
            candidates.append((name, is_regency))

    return candidates
