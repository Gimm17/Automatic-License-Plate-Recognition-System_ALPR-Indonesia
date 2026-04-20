"""
backend/services/plate_validator.py
Indonesian license plate validation and region mapping.
"""

import re
from typing import Optional

# ─── Region Map — 40+ kode wilayah ──────────────────────────────────────────
REGION_MAP: dict[str, str] = {
    # Jawa
    "A":  "Banten",
    "B":  "DKI Jakarta",
    "D":  "Kota Bandung",
    "E":  "Cirebon",
    "F":  "Kota Bogor",
    "G":  "Pekalongan",
    "H":  "Kota Semarang",
    "K":  "Pati",
    "L":  "Kota Surabaya",
    "M":  "Madura",
    "N":  "Malang",
    "P":  "Besuki (Jawa Timur)",
    "R":  "Banyumas",
    "S":  "Bojonegoro",
    "T":  "Karawang",
    "W":  "Gresik",
    "Z":  "Tasikmalaya",
    "AA": "Magelang",
    "AB": "DI Yogyakarta",
    "AD": "Surakarta",
    "AE": "Madiun",
    "AG": "Kediri",

    # Sumatera
    "BA": "Sumatera Barat",
    "BB": "Tapanuli",
    "BD": "Bengkulu",
    "BE": "Lampung",
    "BG": "Sumatera Selatan",
    "BH": "Jambi",
    "BK": "Sumatera Utara",
    "BL": "Aceh",
    "BM": "Riau",
    "BN": "Bangka Belitung",
    "BP": "Kepulauan Riau",

    # Kalimantan
    "DA": "Kalimantan Selatan",
    "KB": "Kalimantan Barat",
    "KH": "Kalimantan Tengah",
    "KT": "Kalimantan Timur",
    "KU": "Kalimantan Utara",

    # Sulawesi
    "DB": "Sulawesi Utara",
    "DC": "Sulawesi Barat",
    "DD": "Sulawesi Selatan",
    "DG": "Sulawesi Selatan",
    "DL": "Sulawesi Utara",
    "DM": "Gorontalo",
    "DN": "Sulawesi Tengah",
    "DT": "Sulawesi Tenggara",

    # Bali & Nusa Tenggara
    "DH": "Nusa Tenggara Timur",
    "DK": "Bali",
    "DR": "Lombok",
    "EA": "Nusa Tenggara Barat",
    "EB": "Nusa Tenggara Timur",
    "ED": "Nusa Tenggara Timur",

    # Maluku & Papua
    "DE": "Maluku",
    "DG": "Maluku Utara",
    "PA": "Papua",
    "PB": "Papua Barat",
    "PE": "Papua Selatan",
    "PG": "Papua Tengah",
    "PL": "Papua Pegunungan",
}

# ─── Regex patterns ───────────────────────────────────────────────────────────
# Standard plate: 1-2 letters  1-4 digits  1-3 letters
PLATE_PATTERN = re.compile(r"^([A-Z]{1,2})\s?(\d{1,4})\s?([A-Z]{1,3})$")

# Special plates: TNI, POLRI, Diplomatic (CD), Presidential (RI), etc.
SPECIAL_PATTERN = re.compile(
    r"^(TNI|POLRI|CD|RF|RFH|RFS|RFP|RFD|RFL|RI)\s?\d+"
)


def clean_ocr_text(raw: str) -> str:
    """
    Clean raw OCR output:
    - Uppercase
    - Remove characters that are not alphanumeric or space
    - Collapse multiple spaces
    """
    text = raw.upper().strip()
    text = re.sub(r"[^A-Z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def validate_plate(raw_text: str) -> dict:
    """
    Validate and enrich a raw OCR plate string.

    Returns:
        {
            "plate":       str,   # cleaned & formatted
            "plate_raw":   str,   # original input
            "valid":       bool,
            "status":      str,   # "valid" | "invalid" | "special"
            "region":      str,
            "region_code": str,
        }
    """
    text = clean_ocr_text(raw_text)

    # ── Special plates ─────────────────────────────────────────────────────
    if SPECIAL_PATTERN.match(text):
        prefix = text.split()[0] if " " in text else text[:max(3, 5)]
        return {
            "plate":       text,
            "plate_raw":   raw_text,
            "valid":       True,
            "status":      "valid",
            "region":      "Kendaraan Dinas Khusus",
            "region_code": prefix,
        }

    # ── Standard plates ────────────────────────────────────────────────────
    match = PLATE_PATTERN.match(text)
    if not match:
        return {
            "plate":       text,
            "plate_raw":   raw_text,
            "valid":       False,
            "status":      "invalid",
            "region":      "Tidak dikenal",
            "region_code": "",
        }

    code        = match.group(1)
    number_part = match.group(2)
    suffix_part = match.group(3)
    region      = REGION_MAP.get(code, "Wilayah tidak terdaftar")
    formatted   = f"{code} {number_part} {suffix_part}"

    return {
        "plate":       formatted,
        "plate_raw":   raw_text,
        "valid":       True,
        "status":      "valid",
        "region":      region,
        "region_code": code,
    }


def format_plate(text: str) -> str:
    """Return the cleaned, space-separated plate string."""
    result = validate_plate(text)
    return result["plate"]
