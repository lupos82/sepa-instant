"""Utilidades comunes: JSON determinista, escritura atómica, normalización de texto."""
import hashlib
import json
import os
import re
import tempfile
import unicodedata
from datetime import date, datetime, timezone


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return date.today().isoformat()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def dumps(obj, pretty=False) -> str:
    if pretty:
        return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def write_json_atomic(path: str, obj, pretty=False) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".tmp-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(dumps(obj, pretty=pretty))
    os.replace(tmp, path)


def read_json(path: str, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm_name(s: str) -> str:
    """Clave de búsqueda: minúsculas, sin tildes ni signos, espacios simples."""
    s = strip_accents(s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def clean(s) -> str:
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()


BIC_RE = re.compile(r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$")


def norm_bic(s) -> str:
    """Normaliza un BIC a 11 caracteres. Devuelve '' si no es válido."""
    b = re.sub(r"\s", "", str(s or "")).upper()
    if not BIC_RE.match(b):
        return ""
    return b if len(b) == 11 else b + "XXX"


LEI_RE = re.compile(r"^[A-Z0-9]{18}[0-9]{2}$")


def norm_lei(s) -> str:
    v = re.sub(r"\s", "", str(s or "")).upper()
    return v if LEI_RE.match(v) else ""


def to_iso_date(v) -> str:
    v = clean(v)
    if not v:
        return ""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", v)
    if m:
        return f"{m[1]}-{m[2]}-{m[3]}"
    m = re.match(r"^(\d{1,2})[/.](\d{1,2})[/.](\d{4})", v)
    if m:
        return f"{m[3]}-{int(m[2]):02d}-{int(m[1]):02d}"
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", v)
    if m:
        return f"{m[1]}-{m[2]}-{m[3]}"
    return ""


def decode_text(raw: bytes, prefer=("utf-8-sig", "utf-16", "cp1252", "latin-1")) -> str:
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    for enc in prefer:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("latin-1", errors="replace")
