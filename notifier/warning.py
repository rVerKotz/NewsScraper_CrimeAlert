import logging
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.box import ASCII

from storage.db import (
    get_crime_articles,
    get_latest_articles,
    save_warning,
)

logger = logging.getLogger(__name__)
console = Console()


def process_new_articles(articles: list) -> int:
    count = 0
    for article in articles:
        if article.relevance_score > 0 and article.url:
            from storage.db import save_article as db_save
            article_id = db_save(article)
            if article_id:
                message = _build_warning_message(article)
                save_warning(article_id, message)
                count += 1
    return count


def _build_warning_message(article) -> str:
    parts = [f"[PERINGATAN] {article.title}"]

    loc_parts = []
    if article.city:
        loc_parts.append(article.city.title())
    if article.province:
        loc_parts.append(article.province)
    if article.latitude and article.longitude:
        loc_parts.append(f"({article.latitude:.4f}, {article.longitude:.4f})")
    if loc_parts:
        parts.append(" | ".join(loc_parts))

    if article.crime_type:
        parts.append(f"[{article.crime_type.upper()}]")
    parts.append(f"Source: {article.source}")
    return " | ".join(parts)


def display_headlines(articles: list[dict], title: str = "Headlines") -> None:
    if not articles:
        console.print(Panel("[yellow]No articles found.[/yellow]", title=title, box=ASCII))
        return

    table = Table(title=title, box=ASCII, show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="bold", width=45)
    table.add_column("City/Province", style="cyan", width=20)
    table.add_column("Coordinates", style="green", width=18)
    table.add_column("Crime", style="yellow", width=12)
    table.add_column("Source", style="blue", width=12)
    table.add_column("Published", style="dim", width=16)

    for i, a in enumerate(articles, 1):
        loc = ""
        if a.get("city"):
            loc = a["city"].title()
        if a.get("province"):
            loc += f", {a['province']}" if loc else a["province"]

        coord = ""
        lat, lon = a.get("latitude") or 0, a.get("longitude") or 0
        if lat and lon:
            coord = f"{lat:.4f}, {lon:.4f}"

        published = (a.get("published") or "")[:16] if a.get("published") else ""

        table.add_row(
            str(i),
            (a.get("title") or "")[:60],
            loc[:30],
            coord,
            a.get("crime_type", ""),
            a.get("source", ""),
            published,
        )

    console.print(table)


def display_warnings(warnings: list[dict]) -> None:
    if not warnings:
        console.print(Panel("[yellow]No warnings.[/yellow]", title="Warnings", box=ASCII))
        return

    table = Table(title="Crime Warnings", box=ASCII, show_lines=True)
    table.add_column("ID", style="dim", width=3)
    table.add_column("Message", style="bold red", width=70)
    table.add_column("Location", style="cyan", width=25)
    table.add_column("Score", style="yellow", width=6)
    table.add_column("Time", style="dim", width=16)

    for w in warnings:
        loc = ""
        if w.get("city"):
            loc = w["city"].title()
        if w.get("province"):
            loc += f", {w['province']}" if loc else w["province"]
        created = (w.get("created_at") or "")[:16]
        score = w.get("relevance_score") or 0
        if isinstance(score, float):
            score_display = f"{score:.0f}"
        else:
            score_display = str(score)

        table.add_row(
            str(w["id"]),
            w.get("message", "")[:100],
            loc[:30],
            score_display,
            created,
        )

    console.print(table)


def display_personalized_feed(prefs: list[dict], articles: list[dict]) -> None:
    if not prefs:
        console.print(Panel("[yellow]No preferences set. Use 'add-region' first.[/yellow]", title="Personalized Feed", box=ASCII))
        return

    for pref in prefs:
        city = pref.get("city", "")
        province = pref.get("province", "")
        crime_type = pref.get("crime_type", "")

        filtered = []
        for a in articles:
            match_city = not city or city.lower() in a.get("city", "").lower()
            match_province = not province or province.lower() in a.get("province", "").lower()
            match_crime = not crime_type or crime_type.lower() in a.get("crime_type", "").lower()
            if match_city and match_province and match_crime:
                filtered.append(a)

        label = " | ".join(filter(None, [city.title() if city else "", province.title() if province else "", crime_type.upper() if crime_type else ""]))
        title = f"Personalized: {label}" if label else "Personalized Feed"
        display_headlines(filtered, title=title)


def display_stats(stats: dict) -> None:
    console.print(Panel(
        f"Total articles: {stats['total']}\n"
        f"Crime articles: {stats['crime_articles']}\n"
        f"Unread: {stats['unread']}",
        title="Statistics",
        box=ASCII,
    ))

    if stats.get("top_cities"):
        table = Table(title="Top Cities", box=ASCII)
        table.add_column("City", style="cyan")
        table.add_column("Count", style="yellow")
        for c in stats["top_cities"]:
            table.add_row(c["city"].title() if c["city"] else "(unknown)", str(c["cnt"]))
        console.print(table)

    if stats.get("top_provinces"):
        table = Table(title="Top Provinces", box=ASCII)
        table.add_column("Province", style="cyan")
        table.add_column("Count", style="yellow")
        for p in stats["top_provinces"]:
            table.add_row(p["province"].title() if p["province"] else "(unknown)", str(p["cnt"]))
        console.print(table)

    if stats.get("top_crimes"):
        table = Table(title="Crime Types", box=ASCII)
        table.add_column("Type", style="yellow")
        table.add_column("Count", style="white")
        for c in stats["top_crimes"]:
            table.add_row(c["crime_type"].upper() if c["crime_type"] else "(unknown)", str(c["cnt"]))
        console.print(table)

    if stats.get("by_source"):
        table = Table(title="By Source", box=ASCII)
        table.add_column("Source", style="blue")
        table.add_column("Count", style="white")
        for s in stats["by_source"]:
            table.add_row(s["source"], str(s["cnt"]))
        console.print(table)
