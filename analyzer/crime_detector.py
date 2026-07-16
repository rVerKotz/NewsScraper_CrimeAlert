import logging
import re
from typing import Optional

from config import CRIME_KEYWORDS, CRIME_CATEGORIES, CITY_COORDS, CITY_ALIASES

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

    for city_name, (province, lat, lon) in CITY_COORDS.items():
        count = text_lower.count(city_name)
        if count > 0:
            found.append((city_name, province, lat, lon, count))

    for alias, canonical in CITY_ALIASES.items():
        if canonical == alias:
            continue
        count = text_lower.count(alias)
        if count > 0:
            province, lat, lon = CITY_COORDS[canonical][0], CITY_COORDS[canonical][1], CITY_COORDS[canonical][2]
            found.append((canonical, province, lat, lon, count))

    for city_name in CITY_COORDS:
        pattern = r"\b(" + re.escape(city_name) + r")\b"
        matches = re.findall(pattern, text_lower)
        count = len(matches)
        if count > 0:
            province, lat, lon = CITY_COORDS[city_name]
            found.append((city_name, province, lat, lon, count))

    if found:
        found.sort(key=lambda x: x[4], reverse=True)
        best = found[0]
        return best[0], best[1], best[2], best[3]

    if "jakarta" in text_lower or "dkj" in text_lower:
        return "jakarta", "DKI Jakarta", -6.2088, 106.8456

    return "", "", 0.0, 0.0


def analyze_article(article) -> None:
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

    if not article.province:
        article.province = ""
    if not article.city:
        article.city = ""
