#!/usr/bin/env python3

import sys
import os
import logging

os.environ["PYTHONIOENCODING"] = "utf-8"

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt

from storage.db import init_db, get_stats, get_warnings
from storage.db import add_user_preference, get_user_preferences, remove_user_preference
from storage.db import get_crime_articles, get_latest_articles
from scraper import get_all_scrapers
from analyzer.crime_detector import analyze_article
from notifier.warning import (
    process_new_articles,
    display_headlines,
    display_warnings,
    display_personalized_feed,
    display_stats,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

console = Console(force_terminal=True, legacy_windows=True)
from rich import box
ASCII_BOX = box.ASCII2
logger = logging.getLogger(__name__)


def cmd_scrape():
    console.print("[bold cyan]Memulai scraping berita kriminal...[/bold cyan]")
    scrapers = get_all_scrapers()
    total = 0
    crime_count = 0

    for name, scraper in scrapers.items():
        console.print(f"\n[bold]Mengambil berita dari [yellow]{name}[/yellow]...[/bold]")
        try:
            articles = scraper.scrape()
            console.print(f"  Mendapatkan {len(articles)} artikel mentah")

            for article in articles:
                analyze_article(article)

            crime_articles = [a for a in articles if a.relevance_score > 0]
            crime_count += len(crime_articles)
            total += len(articles)
            console.print(f"  [red]{len(crime_articles)} terkait kriminal![/red]")

        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")
            logger.exception("Scrape error")

    console.print(f"\n[bold green]Selesai![/bold green] Total {total} artikel, {crime_count} terkait kriminal.")


def cmd_headlines():
    warnings = get_warnings(limit=20)
    if not warnings:
        console.print("[yellow]Belum ada peringatan.[/yellow]")
        return

    table = Table(title="Headline Peringatan Kejahatan", border_style="red", box=ASCII_BOX)
    table.add_column("#", style="dim")
    table.add_column("Waktu", style="cyan")
    table.add_column("Lokasi", style="yellow")
    table.add_column("Koordinat", style="green")
    table.add_column("Jenis", style="magenta")
    table.add_column("Pesan", style="white", no_wrap=False)
    table.add_column("Sumber", style="blue")

    for i, w in enumerate(warnings[:15], 1):
        loc = ""
        if w.get("city"):
            loc = w["city"].title()
        if w.get("province"):
            loc += f", {w['province']}" if loc else w["province"]
        coord = ""
        if w.get("latitude") and w.get("longitude"):
            coord = f"{w['latitude']:.4f}, {w['longitude']:.4f}"

        table.add_row(
            str(i),
            (w.get("created_at") or "")[-8:],
            loc[:25] or "-",
            coord[:18],
            w.get("crime_type", "-"),
            (w.get("message") or "")[:55],
            w.get("source", "-"),
        )

    console.print(table)

    for w in warnings[:5]:
        console.print(f"\n[bold red]{w['message']}[/bold red]")
        console.print(f"   Link: {w.get('url', '')}")


def cmd_personalized(region: str = ""):
    if region:
        prefs = [{"city": region, "province": "", "crime_type": ""}]
    else:
        prefs = get_user_preferences()
        if not prefs:
            console.print("[yellow]Belum ada preferensi. Gunakan 'add-region' dulu.[/yellow]")
            return

    articles = get_crime_articles(limit=50)
    display_personalized_feed(prefs, articles)


def cmd_stats():
    stats = get_stats()
    display_stats(stats)


def cmd_add_region(region: str, crime_type: str = ""):
    from config import CITY_COORDS
    region_lower = region.lower().strip()
    city = ""
    province = ""
    if region_lower in CITY_COORDS:
        city = region_lower
        province = CITY_COORDS[region_lower][0]
    from config import CITY_ALIASES
    if region_lower in CITY_ALIASES and CITY_ALIASES[region_lower] != region_lower:
        canonical = CITY_ALIASES[region_lower]
        city = canonical
        province = CITY_COORDS.get(canonical, ("",))[0]

    add_user_preference(city=city, province=province, crime_type=crime_type)
    display = " | ".join(filter(None, [province or region.title(), crime_type]))
    console.print(f"[green]Preferensi [bold]{display}[/bold] ditambahkan![/green]")


def cmd_list_regions():
    prefs = get_user_preferences()
    if not prefs:
        console.print("[yellow]Belum ada preferensi wilayah.[/yellow]")
        return

    table = Table(title="Preferensi Wilayah", border_style="green", box=ASCII_BOX)
    table.add_column("ID", style="dim")
    table.add_column("Provinsi", style="cyan")
    table.add_column("Kota", style="yellow")
    table.add_column("Jenis", style="magenta")
    table.add_column("Ditambahkan", style="white")

    for p in prefs:
        table.add_row(
            str(p["id"]),
            p.get("province", "").title() or "-",
            p.get("city", "").title() or "-",
            p.get("crime_type", "-"),
            (p.get("created_at") or "")[:16],
        )

    console.print(table)


def cmd_interactive():
    init_db()
    console.clear()
    console.print(Panel.fit(
        "[bold red]SISTEM PERINGATAN BERITA KRIMINAL INDONESIA[/bold red]\n"
        "[dim]- Pemantauan Curanmor & Kejahatan Jalanan[/dim]\n"
        "[dim]- Sumber: CNN Indonesia, Detik.com, Sindonews[/dim]",
        border_style="red",
    ))

    while True:
        menu = Table.grid(padding=1)
        menu.add_column()
        menu.add_row("[1] Scrape Berita Terbaru")
        menu.add_row("[2] Lihat Headline/Peringatan")
        menu.add_row("[3] Berita Personalisasi")
        menu.add_row("[4] Statistik")
        menu.add_row("[5] Kelola Preferensi Wilayah")
        menu.add_row("[6] Jalankan API Server (FastAPI, gunakan Swagger)")
        menu.add_row("[7] Keluar")

        console.print("\n" + "-" * 50)
        console.print(menu)
        console.print("-" * 50)

        choice = Prompt.ask("[bold cyan]Pilih menu", choices=["1", "2", "3", "4", "5", "6", "7"])

        if choice == "1":
            cmd_scrape()
        elif choice == "2":
            cmd_headlines()
        elif choice == "3":
            console.print("[dim]Masukkan nama wilayah (kosongkan untuk semua preferensi):[/dim]")
            region = Prompt.ask("Wilayah", default="")
            cmd_personalized(region)
        elif choice == "4":
            cmd_stats()
        elif choice == "5":
            cmd_region_menu()
        elif choice == "6":
            cmd_serve()
        elif choice == "7":
            console.print("[yellow]Terima kasih! Tetap waspada.[/yellow]")
            break

        Prompt.ask("\n[dim]Tekan Enter untuk melanjutkan...[/dim]", default="")


def cmd_region_menu():
    while True:
        console.print("\n[bold cyan]KELOLA PREFERENSI WILAYAH[/bold cyan]")
        console.print("[1] Lihat Preferensi")
        console.print("[2] Tambah Wilayah")
        console.print("[3] Hapus Wilayah")
        console.print("[4] Kembali")

        choice = Prompt.ask("Pilih", choices=["1", "2", "3", "4"])

        if choice == "1":
            cmd_list_regions()
        elif choice == "2":
            region = Prompt.ask("Nama kota (contoh: jakarta, bandung, surabaya)")
            crime_type = Prompt.ask("Jenis kejahatan (kosongkan untuk semua)", default="")
            cmd_add_region(region, crime_type)
        elif choice == "3":
            cmd_list_regions()
            pref_id = IntPrompt.ask("ID preferensi yang akan dihapus")
            remove_user_preference(pref_id)
            console.print(f"[green]Preferensi ID {pref_id} dihapus.[/green]")
        elif choice == "4":
            break


def cmd_serve():
    import uvicorn
    from app.settings_manager import settings as app_settings
    host = app_settings.get("api_host", "0.0.0.0")
    port = app_settings.get("api_port", 8000)
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            pass
    if len(sys.argv) > 3:
        host = sys.argv[3]
    console.print(f"[bold green]API server at http://{host}:{port}[/bold green]")
    console.print("[dim]Swagger docs at http://{}:{}/docs[/dim]".format(host, port))
    console.print("[dim]Endpoints: GET /api/health, GET/PUT /api/settings, POST /api/settings/reset, POST /api/scrape, GET /api/sources, GET /api/cities[/dim]")
    uvicorn.run("app.api:app", host=host, port=port, reload=False)


def main():
    if len(sys.argv) < 2:
        cmd_interactive()
        return

    command = sys.argv[1]
    if command != "serve":
        init_db()

    commands = {
        "scrape": cmd_scrape,
        "serve": cmd_serve,
        "headlines": cmd_headlines,
        "personalized": lambda: cmd_personalized(sys.argv[2] if len(sys.argv) > 2 else ""),
        "stats": cmd_stats,
        "add-region": lambda: cmd_add_region(
            sys.argv[2] if len(sys.argv) > 2 else "",
            sys.argv[3] if len(sys.argv) > 3 else "",
        ),
        "regions": cmd_list_regions,
        "interactive": cmd_interactive,
    }

    cmd = commands.get(command)
    if cmd:
        cmd()
    else:
        console.print(f"[red]Perintah tidak dikenal: {command}[/red]")
        console.print("Perintah yang tersedia: scrape, headlines, personalized, stats, add-region, regions, serve, interactive")
        sys.exit(1)


if __name__ == "__main__":
    main()
