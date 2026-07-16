# NewsScraper CrimeAlert

Sistem scraping dan peringatan berita kriminal Indonesia, khusus pemantauan **curanmor** (pencurian sepeda motor), begal, dan kejahatan jalanan dari CNN Indonesia, Detik.com, dan Sindonews.

## Fitur

- **Scraping otomatis** berita dari 3 sumber dengan deteksi kejahatan berbasis keyword
- **Klasifikasi lokasi** — ekstrak kota, provinsi, dan koordinat GPS dari teks artikel (140+ kota Indonesia)
- **Peringatan kriminal** — skor relevansi otomatis untuk setiap artikel
- **Personalisasi wilayah** — filter berita berdasarkan kota/provinsi preferensi
- **CLI interaktif** — menu berbasis Rich console
- **REST API** — FastAPI untuk integrasi eksternal
- **Supabase support** — push hasil scraping langsung ke database Supabase Anda

## Sumber Berita

| Sumber | URL | Metode |
|--------|-----|--------|
| CNN Indonesia | `cnnindonesia.com/tag/curanmor` | Tag URL |
| Detik.com | `detik.com/tag/curanmor` | Tag URL |
| Sindonews | `sindonews.com/topic/1640/curanmor` | Topic URL |

## Instalasi

```bash
git clone https://github.com/yourusername/NewsScraper_CrimeAlert.git
cd NewsScraper_CrimeAlert
pip install -r requirements.txt
```

Untuk fitur Supabase (opsional):
```bash
pip install supabase-py
```

## Cara Pakai

### CLI Interaktif

```bash
python main.py
```

### Perintah CLI

```bash
# Scrape berita terbaru
python main.py scrape

# Lihat peringatan
python main.py headlines

# Statistik database
python main.py stats

# Tambah preferensi wilayah
python main.py add-region jakarta curanmor

# Daftar preferensi
python main.py regions

# Berita personalisasi
python main.py personalized

# Jalankan API server
python main.py serve 8000
```

### REST API

Jalankan server:
```bash
python main.py serve 8000
```

Semua endpoint ada di `http://localhost:8000/docs` (Swagger UI).

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/api/health` | Status server & konfigurasi DB |
| GET | `/api/settings` | Lihat settings saat ini |
| PUT | `/api/settings` | Ubah settings (interval, max articles, Supabase credentials) |
| POST | `/api/settings/reset` | Reset ke default |
| POST | `/api/scrape` | Jalankan scraping → push ke Supabase jika dikonfigurasi |
| GET | `/api/articles` | Filter artikel (source, city, province, crime_type) |
| GET | `/api/articles/latest` | Artikel terbaru |
| GET | `/api/stats` | Statistik database |
| GET | `/api/warnings` | Daftar peringatan |
| GET | `/api/sources` | Daftar scraper tersedia |
| GET | `/api/cities` | Daftar kota + koordinat |
| GET/POST/DELETE | `/api/preferences` | Kelola preferensi wilayah |

**Contoh konfigurasi Supabase:**
```bash
curl -X PUT http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "supabase_url": "https://your-project.supabase.co",
    "supabase_service_role_key": "your-service-role-key",
    "supabase_table": "crime_articles",
    "max_articles_per_source": 15
  }'
```

**Contoh trigger scrape:**
```bash
curl -X POST http://localhost:8000/api/scrape
```

### Database: Local vs Supabase

**Local (default):** Semua hasil scraping disimpan di `data/crime_news.db` (SQLite).  
**Supabase:** Set credentials via `PUT /api/settings`, maka hasil scrape akan di-push ke tabel Supabase Anda. Tabel akan dibuat otomatis dengan kolom: `url`, `title`, `source`, `summary`, `content`, `published`, `province`, `city`, `latitude`, `longitude`, `crime_type`, `relevance_score`, `scraped_at`.

### Jadwal Scraping (Opsional)

Server tidak menjadwalkan scraping otomatis. Gunakan cron (Linux) atau Task Scheduler (Windows):

```bash
# Setiap 6 jam
0 */6 * * * curl -X POST http://localhost:8000/api/scrape
```

## Struktur Proyek

```
NewsScraper_CrimeAlert/
├── app/
│   ├── api.py               # FastAPI routes & server
│   ├── settings_manager.py  # Settings persisten (JSON)
│   └── supabase_client.py   # Supabase push client
├── analyzer/
│   └── crime_detector.py    # Klasifikasi kejahatan & ekstraksi lokasi
├── scraper/
│   ├── base.py              # Base scraper (HTTP session, Article dataclass)
│   ├── cnn_indonesia.py     # Scraper CNN Indonesia
│   ├── detik.py             # Scraper Detik.com
│   └── sindonews.py         # Scraper Sindonews
├── storage/
│   └── db.py                # SQLite database layer
├── notifier/
│   └── warning.py           # Warning generator + Rich display
├── config.py                # Keywords, city coordinates, constants
├── main.py                  # CLI entry point
├── requirements.txt
└── README.md
```

## Koordinat Kota

Setiap kota memiliki koordinat GPS terpusat (alun-alun kota/mapolres terdekat). Sistem mengekstrak kota dari teks artikel dan mengisi kolom `latitude`/`longitude` secara otomatis. 140+ kota tercakup dari Aceh hingga Papua.

## License

MIT
