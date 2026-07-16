import logging
import re
from typing import Optional

from config import CRIME_KEYWORDS, CRIME_CATEGORIES, CITY_COORDS, CITY_ALIASES
from scraper.base import normalize_article

logger = logging.getLogger(__name__)


def classify_crime(text: str) -> tuple[str, float]:
    text_lower = text.lower()
    scores: dict[str, float] = {}
    for category, keywords in CRIME_CATEGORIES.items():
        score = 0
        for kw in keywords:
            count = text_lower.count(kw.lower())
            if count > 0:
                score += count * (10 if category == "curanmor" else 8)
                if kw.startswith("curanmor") or kw.startswith("pencurian motor"):
                    score += 5
        if score > 0:
            scores[category] = score

    if not scores:
        for kw in CRIME_KEYWORDS:
            count = text_lower.count(kw.lower())
            if count > 0:
                ref_score = 10 if "curanmor" in kw or "motor" in kw or "sepeda motor" in kw else 5
                scores["pencurian"] = scores.get("pencurian", 0) + count * ref_score

    if scores:
        best = max(scores, key=scores.get)
        return best, scores[best]
    return "", 0.0


def extract_location(text: str) -> tuple[str, str, float, float]:
    text_lower = text.lower()
    found: list[tuple[str, str, float, float, int]] = []

    def add_city(city_name: str, count: int = 1):
        if count <= 0:
            return
        province, lat, lon = CITY_COORDS[city_name]
        found.append((city_name, province, lat, lon, count))

    for city_name in CITY_COORDS:
        pattern = r"\b(" + re.escape(city_name) + r")\b"
        matches = re.findall(pattern, text_lower)
        count = len(matches)
        if count > 0:
            add_city(city_name, count)

    for alias, canonical in CITY_ALIASES.items():
        if canonical == alias or canonical not in CITY_COORDS:
            continue
        count = len(re.findall(r"\b" + re.escape(alias) + r"\b", text_lower))
        if count > 0:
            add_city(canonical, count)

    for prefix in ["kota ", "kabupaten ", "kecamatan ", "kelurahan ", "desa "]:
        for city_name in CITY_COORDS:
            pattern = re.escape(prefix) + r"\b" + re.escape(city_name) + r"\b"
            count = len(re.findall(pattern, text_lower))
            if count > 0:
                add_city(city_name, count)

    for sub in ["utara", "selatan", "timur", "barat", "pusat"]:
        for city_name in CITY_COORDS:
            pattern = re.escape(city_name) + r"\s+" + re.escape(sub) + r"\b"
            matches = re.findall(pattern, text_lower)
            if matches:
                add_city(city_name, len(matches))

    if found:
        found.sort(key=lambda x: x[4], reverse=True)
        best = found[0]
        return best[0], best[1], best[2], best[3]

    if "jakarta" in text_lower or "dkj" in text_lower:
        return "jakarta", "DKI Jakarta", -6.2088, 106.8456

    return "", "", 0.0, 0.0


def analyze_article(article) -> None:
    normalize_article(article)
    combined = f"{article.title} {article.summary} {article.content}".strip()
    if not combined:
        combined = f"{article.title} {article.summary}"

    crime_type, score = classify_crime(combined)
    article.crime_type = crime_type
    article.relevance_score = score

    city, province, lat, lon = extract_location(combined)
    article.city = city
    article.province = province
    article.latitude = lat
    article.longitude = lon

    normalize_article(article)
