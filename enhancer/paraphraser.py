import re
import logging
import nltk
import nlpaug.augmenter.word as naw
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

_synonym_aug = None
_random_aug = None
_trans_id_en = None
_trans_en_id = None

POLA_IKLAN_INLINE = re.compile(
    r"\s*(?:"
    r"ADVERTISEMENT\s*(?:SCROLL\s*TO\s*CONTINUE(?:\s*WITH\s*CONTENT)?)?|"
    r"SCROLL\s*TO\s*CONTINUE(?:\s*WITH\s*CONTENT)?|"
    r"\bBACA\s+JUGA\s*[:\-][^.\n]*[.\n]|"
    r"\bILUSTRASI\s*[:\-][^.\n]*[.\n]|"
    r"\b(?:Penulis|Editor|Reporter|Kontributor)\s*[:\-]"
    r")\s*",
    re.IGNORECASE,
)

POLA_BARIS_IKLAN = re.compile(
    r"^\s*(?:"
    r"ADVERTISEMENT|"
    r"SCROLL\s*TO\s*CONTINUE(?:\s*WITH\s*CONTENT)?|"
    r"BACA\s+JUGA\s*[:\-].*|"
    r"ILUSTRASI\s*[:\-].*|"
    r"Artikel\s+ini\s+telah\s+tayang\s+di.*|"
    r"(?:Penulis|Editor|Reporter|Kontributor)\s*[:\-].*|"
    r"[*_\-]{3,}"
    r")\s*$",
    re.IGNORECASE,
)


def _init_nltk():
    try:
        nltk.data.find("corpora/wordnet")
    except LookupError:
        nltk.download("wordnet", quiet=True)


def _get_synonym_aug():
    global _synonym_aug
    if _synonym_aug is None:
        _init_nltk()
        _synonym_aug = naw.SynonymAug(aug_src="wordnet", aug_p=0.7, aug_min=2)
    return _synonym_aug


def _get_random_aug():
    global _random_aug
    if _random_aug is None:
        _random_aug = naw.RandomWordAug(action="swap", aug_p=0.3)
    return _random_aug


def _get_trans_id_en():
    global _trans_id_en
    if _trans_id_en is None:
        _trans_id_en = GoogleTranslator(source="id", target="en")
    return _trans_id_en


def _get_trans_en_id():
    global _trans_en_id
    if _trans_en_id is None:
        _trans_en_id = GoogleTranslator(source="en", target="id")
    return _trans_en_id


def _bersihkan_teks(teks: str) -> str:
    if not teks:
        return teks

    teks = POLA_IKLAN_INLINE.sub(" ", teks)
    teks = re.sub(r"\s+", " ", teks)

    baris = teks.split("\n")
    bersih = [b for b in baris if not POLA_BARIS_IKLAN.match(b.strip())]
    return "\n".join(bersih).strip()


def _pisahkan_paragraf(teks: str) -> tuple[list[str], str]:
    if "\n\n" in teks:
        return teks.split("\n\n"), "\n\n"
    if "\n" in teks:
        return teks.split("\n"), "\n"
    return [teks], ""


def _parafrase_satu_paragraf(teks: str) -> str:
    syn = _get_synonym_aug()
    rnd = _get_random_aug()
    try:
        hasil = syn.augment(teks)
        hasil = hasil if isinstance(hasil, str) else hasil[0]
        hasil = rnd.augment(hasil)
        return hasil if isinstance(hasil, str) else hasil[0]
    except Exception:
        return teks


def parafrase_teks(teks_asli: str) -> str:
    if not teks_asli or not teks_asli.strip():
        return teks_asli

    try:
        teks_asli = _bersihkan_teks(teks_asli)
        if not teks_asli:
            return teks_asli

        paragraf, sep = _pisahkan_paragraf(teks_asli)
        hasil = []

        for par in paragraf:
            stripped = par.strip()
            if not stripped:
                hasil.append(par)
                continue

            try:
                par_en = _get_trans_id_en().translate(stripped)
                par_en_pr = _parafrase_satu_paragraf(par_en)
                par_id = _get_trans_en_id().translate(par_en_pr)
                hasil.append(par_id)
            except Exception:
                hasil.append(stripped)

        return sep.join(hasil)

    except Exception as e:
        logger.warning("Paraphrase gagal, fallback ke teks asli: %s", e)
        return teks_asli
