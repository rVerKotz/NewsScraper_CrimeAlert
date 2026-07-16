import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "crime_news.db"

DATA_DIR.mkdir(exist_ok=True)

REQUEST_TIMEOUT = 15
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

CRIME_KEYWORDS = [
    "curanmor", "pencurian motor", "curi motor", "maling motor",
    "gasak motor", "curi kendaraan", "pencurian kendaraan",
    "curi sepeda motor", "pencurian sepeda motor",
    "motor raib", "motor hilang",
    "kunci T", "kunci leter T", "kunci letter T",
    "spesialis curanmor", "komplotan curanmor",
    "residivis curanmor", "modus curanmor",
    "pencurian", "maling", "gasak", "menggasak",
    "ditangkap polisi", "diringkus", "dicokok",
    "tersangka", "pelaku pencurian",
    "barang bukti", "tahanan",
    "begal", "pembegalan", "begal motor",
    "jambret", "rampok", "perampokan",
    "bobol", "pembobolan",
]

CRIME_CATEGORIES = {
    "curanmor": [
        "curanmor", "curi motor", "curi sepeda motor",
        "pencurian motor", "pencurian sepeda motor",
        "maling motor", "gasak motor", "motor raib",
        "kunci T", "kunci leter T", "spesialis curanmor",
    ],
    "begal": ["begal", "pembegalan", "begal motor", "begal hp"],
    "curat/curas": ["curat", "curas", "pemberatan", "kekerasan"],
    "pencurian": ["pencurian", "maling", "mencuri", "curi", "gasak"],
    "perampokan": ["perampokan", "rampok", "merampok"],
    "pembobolan": ["bobol", "pembobolan", "bongkar"],
}

MAX_ARTICLES_PER_SOURCE = 30
SCRAPE_INTERVAL_MINUTES = 15

# City -> (province, latitude, longitude)
# Coordinates centered on main square/kantor polisi umum
CITY_COORDS = {
    "jakarta": ("DKI Jakarta", -6.2088, 106.8456),
    "jakpus": ("DKI Jakarta", -6.1818, 106.8344),
    "jakbar": ("DKI Jakarta", -6.1683, 106.7585),
    "jaksel": ("DKI Jakarta", -6.2615, 106.8108),
    "jakut": ("DKI Jakarta", -6.1528, 106.8768),
    "jaktim": ("DKI Jakarta", -6.2252, 106.8948),
    "bandung": ("Jawa Barat", -6.9175, 107.6191),
    "bandung barat": ("Jawa Barat", -6.8333, 107.5333),
    "bekasi": ("Jawa Barat", -6.2383, 106.9932),
    "bogor": ("Jawa Barat", -6.5971, 106.8060),
    "depok": ("Jawa Barat", -6.4025, 106.7942),
    "tangerang": ("Banten", -6.1783, 106.6319),
    "tangerang selatan": ("Banten", -6.2889, 106.7181),
    "cilegon": ("Banten", -6.0035, 106.0114),
    "serang": ("Banten", -6.1149, 106.1503),
    "surabaya": ("Jawa Timur", -7.2575, 112.7521),
    "malang": ("Jawa Timur", -7.9797, 112.6304),
    "kediri": ("Jawa Timur", -7.8184, 112.0159),
    "blitar": ("Jawa Timur", -8.0956, 112.1625),
    "madiun": ("Jawa Timur", -7.6298, 111.5231),
    "ponorogo": ("Jawa Timur", -7.8701, 111.4627),
    "jember": ("Jawa Timur", -8.1724, 113.6990),
    "banyuwangi": ("Jawa Timur", -8.2188, 114.3671),
    "sidoarjo": ("Jawa Timur", -7.4530, 112.7190),
    "gresik": ("Jawa Timur", -7.1565, 112.6559),
    "pasuruan": ("Jawa Timur", -7.6457, 112.9068),
    "probolinggo": ("Jawa Timur", -7.7545, 113.2159),
    "mojokerto": ("Jawa Timur", -7.4700, 112.4334),
    "tuban": ("Jawa Timur", -6.8975, 112.0503),
    "bojonegoro": ("Jawa Timur", -7.1547, 111.8832),
    "lamongan": ("Jawa Timur", -7.1233, 112.4190),
    "ngawi": ("Jawa Timur", -7.4039, 111.4476),
    "semarang": ("Jawa Tengah", -6.9932, 110.4203),
    "surakarta": ("Jawa Tengah", -7.5562, 110.8317),
    "solo": ("Jawa Tengah", -7.5562, 110.8317),
    "magelang": ("Jawa Tengah", -7.4706, 110.2181),
    "pekalongan": ("Jawa Tengah", -6.8886, 109.6742),
    "tegal": ("Jawa Tengah", -6.8696, 109.1380),
    "purwokerto": ("Jawa Tengah", -7.4283, 109.2454),
    "salatiga": ("Jawa Tengah", -7.3303, 110.5080),
    "kudus": ("Jawa Tengah", -6.8044, 110.8402),
    "pati": ("Jawa Tengah", -6.7416, 111.0358),
    "demak": ("Jawa Tengah", -6.8941, 110.6386),
    "klaten": ("Jawa Tengah", -7.7105, 110.6059),
    "boyolali": ("Jawa Tengah", -7.5333, 110.6000),
    "sragen": ("Jawa Tengah", -7.4282, 111.0220),
    "wonogiri": ("Jawa Tengah", -7.8118, 110.9260),
    "karanganyar": ("Jawa Tengah", -7.5967, 110.9500),
    "sukoharjo": ("Jawa Tengah", -7.6833, 110.8333),
    "yogyakarta": ("D I Yogyakarta", -7.7956, 110.3695),
    "jogja": ("D I Yogyakarta", -7.7956, 110.3695),
    "sleman": ("D I Yogyakarta", -7.7150, 110.3556),
    "bantul": ("D I Yogyakarta", -7.9000, 110.3333),
    "gunung kidul": ("D I Yogyakarta", -7.9667, 110.6000),
    "kulon progo": ("D I Yogyakarta", -7.8333, 110.1667),
    "medan": ("Sumatera Utara", 3.5952, 98.6722),
    "binjai": ("Sumatera Utara", 3.6133, 98.4983),
    "tebing tinggi": ("Sumatera Utara", 3.3300, 99.1600),
    "pematangsiantar": ("Sumatera Utara", 2.9600, 99.0600),
    "tanjung balai": ("Sumatera Utara", 2.9583, 99.8000),
    "sibolga": ("Sumatera Utara", 1.7417, 98.7833),
    "padang sidempuan": ("Sumatera Utara", 1.3800, 99.2800),
    "gunungsitoli": ("Sumatera Utara", 1.2833, 97.6167),
    "kisaran": ("Sumatera Utara", 3.0000, 99.8167),
    "rantau prapat": ("Sumatera Utara", 2.1000, 99.8333),
    "padang": ("Sumatera Barat", -0.9471, 100.4172),
    "bukittinggi": ("Sumatera Barat", -0.3056, 100.3694),
    "padang panjang": ("Sumatera Barat", -0.4667, 100.4000),
    "sawahlunto": ("Sumatera Barat", -0.6833, 100.7833),
    "solok": ("Sumatera Barat", -0.8000, 100.6500),
    "payakumbuh": ("Sumatera Barat", -0.2167, 100.6333),
    "pekanbaru": ("Riau", 0.5071, 101.4478),
    "dumai": ("Riau", 1.6833, 101.4500),
    "tembilahan": ("Riau", -0.3167, 103.1500),
    "batam": ("Kepulauan Riau", 1.1281, 104.0355),
    "tanjung pinang": ("Kepulauan Riau", 0.9167, 104.4500),
    "tanjung balai karimun": ("Kepulauan Riau", 1.0000, 103.4167),
    "jambi": ("Jambi", -1.5900, 103.6100),
    "sungai penuh": ("Jambi", -2.0667, 101.3833),
    "palembang": ("Sumatera Selatan", -2.9761, 104.7754),
    "lubuklinggau": ("Sumatera Selatan", -3.2950, 102.8610),
    "prabumulih": ("Sumatera Selatan", -3.4333, 104.2333),
    "pagar alam": ("Sumatera Selatan", -4.0167, 103.2500),
    "baturaja": ("Sumatera Selatan", -4.1333, 104.1667),
    "lampung": ("Lampung", -5.4296, 105.2614),
    "bandar lampung": ("Lampung", -5.4296, 105.2614),
    "metro": ("Lampung", -5.1167, 105.3000),
    "kota bumi": ("Lampung", -4.9000, 105.3333),
    "bengkulu": ("Bengkulu", -3.8005, 102.2655),
    "curup": ("Bengkulu", -3.4667, 102.5333),
    "pangkal pinang": ("Bangka Belitung", -2.1333, 106.1167),
    "sungailiat": ("Bangka Belitung", -1.8500, 106.1167),
    "tanjung pandan": ("Bangka Belitung", -2.7500, 107.6500),
    "pontianak": ("Kalimantan Barat", -0.0263, 109.3425),
    "singkawang": ("Kalimantan Barat", 0.9000, 108.9833),
    "ketapang": ("Kalimantan Barat", -1.8500, 109.9833),
    "sintang": ("Kalimantan Barat", 0.0667, 111.4833),
    "palangkaraya": ("Kalimantan Tengah", -2.2137, 113.9123),
    "sampit": ("Kalimantan Tengah", -2.5333, 112.9500),
    "kuala kapuas": ("Kalimantan Tengah", -3.0000, 114.3667),
    "banjarmasin": ("Kalimantan Selatan", -3.3186, 114.5944),
    "banjarbaru": ("Kalimantan Selatan", -3.4500, 114.8333),
    "martapura": ("Kalimantan Selatan", -3.4167, 114.8500),
    "tanjung": ("Kalimantan Selatan", -2.1333, 115.3667),
    "samarinda": ("Kalimantan Timur", -0.5022, 117.1536),
    "balikpapan": ("Kalimantan Timur", -1.2635, 116.8278),
    "bontang": ("Kalimantan Timur", 0.1333, 117.5000),
    "tarakan": ("Kalimantan Utara", 3.3000, 117.6333),
    "tanjung selor": ("Kalimantan Utara", 2.8500, 117.3667),
    "manado": ("Sulawesi Utara", 1.4917, 124.8428),
    "bitung": ("Sulawesi Utara", 1.4500, 125.2000),
    "tomohon": ("Sulawesi Utara", 1.3167, 124.8333),
    "kotamobagu": ("Sulawesi Utara", 0.7333, 124.3167),
    "gorontalo": ("Gorontalo", 0.5333, 123.0667),
    "palu": ("Sulawesi Tengah", -0.9011, 119.8598),
    "poso": ("Sulawesi Tengah", -1.3833, 120.7500),
    "luwuk": ("Sulawesi Tengah", -0.9500, 122.7833),
    "makassar": ("Sulawesi Selatan", -5.1477, 119.4327),
    "parepare": ("Sulawesi Selatan", -4.0167, 119.6167),
    "palopo": ("Sulawesi Selatan", -2.9833, 120.2000),
    "watampone": ("Sulawesi Selatan", -4.5333, 120.3333),
    "pinrang": ("Sulawesi Selatan", -3.7833, 119.6500),
    "kendari": ("Sulawesi Tenggara", -3.9722, 122.5947),
    "baubau": ("Sulawesi Tenggara", -5.4667, 122.6167),
    "kolaka": ("Sulawesi Tenggara", -4.0500, 121.6000),
    "ambon": ("Maluku", -3.6556, 128.1908),
    "ternate": ("Maluku Utara", 0.7833, 127.3667),
    "tidore": ("Maluku Utara", 0.6833, 127.4000),
    "soasio": ("Maluku Utara", 0.7833, 127.3500),
    "jayapura": ("Papua", -2.5333, 140.7000),
    "merauke": ("Papua Selatan", -8.5000, 140.4000),
    "nabire": ("Papua Tengah", -3.3667, 135.5000),
    "sorong": ("Papua Barat Daya", -0.8667, 131.2500),
    "manokwari": ("Papua Barat", -0.8667, 134.0667),
    "fakfak": ("Papua Barat", -2.9167, 132.3000),
    "timika": ("Papua Tengah", -4.5500, 136.8833),
    "wamena": ("Papua Pegunungan", -4.1000, 138.9500),
    "denpasar": ("Bali", -8.6563, 115.2191),
    "tabanan": ("Bali", -8.5333, 115.0667),
    "singaraja": ("Bali", -8.1167, 115.0833),
    "mataram": ("Nusa Tenggara Barat", -8.5833, 116.1167),
    "bima": ("Nusa Tenggara Barat", -8.4667, 118.7333),
    "dompu": ("Nusa Tenggara Barat", -8.5333, 118.4667),
    "kupang": ("Nusa Tenggara Timur", -10.1772, 123.6070),
    "ende": ("Nusa Tenggara Timur", -8.8333, 121.6500),
    "maumere": ("Nusa Tenggara Timur", -8.6167, 122.2000),
    "waingapu": ("Nusa Tenggara Timur", -9.6500, 120.2667),
    "kefamenanu": ("Nusa Tenggara Timur", -9.4500, 124.4833),
    "aceh": ("Aceh", 5.5500, 95.3172),
    "banda aceh": ("Aceh", 5.5500, 95.3172),
    "lhokseumawe": ("Aceh", 5.1833, 97.1500),
    "langsa": ("Aceh", 4.4667, 97.9667),
    "sabang": ("Aceh", 5.8936, 95.3144),
}

# Alias mapping: various spellings -> canonical city name
CITY_ALIASES = {}
for canonical, (prov, lat, lon) in CITY_COORDS.items():
    CITY_ALIASES[canonical] = canonical
# Add aliases
CITY_ALIASES["jakarta pusat"] = "jakpus"
CITY_ALIASES["jakarta barat"] = "jakbar"
CITY_ALIASES["jakarta selatan"] = "jaksel"
CITY_ALIASES["jakarta utara"] = "jakut"
CITY_ALIASES["jakarta timur"] = "jaktim"
CITY_ALIASES["solo"] = "surakarta"
CITY_ALIASES["jogja"] = "yogyakarta"
CITY_ALIASES["bandar lampung"] = "lampung"
