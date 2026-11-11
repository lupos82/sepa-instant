"""Per-bank-code source dates, never global directory observation churn.

Production audit only: a historical public catalogue may supply the source date
for UNCHANGED codes, but the real, current catalogue always provides bank data.
The caller must separately authenticate the historical bytes against the active
FTPS manifest before any release is planned or approved.
"""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re

_COUNTRY = re.compile(r"^[A-Z]{2}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_CATALOG_BYTES = 1_000_000


def load_published_catalog(root: Path, country: str) -> dict:
    if not _COUNTRY.fullmatch(country):
        raise ValueError("Invalid bank country")
    path = root / (country + ".json")
    if path.is_symlink() or not path.is_file():
        raise ValueError("Published bank snapshot is not a regular file")
    if path.stat().st_size > MAX_CATALOG_BYTES:
        raise ValueError("Published bank snapshot exceeds size limit")
    with path.open("rb") as f:
        payload = f.read(MAX_CATALOG_BYTES + 1)
    if len(payload) > MAX_CATALOG_BYTES:
        raise ValueError("Published bank snapshot exceeds size limit")
    try:
        bank = json.loads(payload)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Published bank snapshot is not JSON") from exc
    if not isinstance(bank, dict) or bank.get("country") != country or (
            bank.get("relation") != "OFFICIAL_LIST") or not isinstance(
            bank.get("codes"), dict):
        raise ValueError("Published bank snapshot has an invalid country/schema")
    stamp = bank.get("effective_date")
    if not isinstance(stamp, str) or not _DATE.fullmatch(stamp):
        raise ValueError("Published bank snapshot has no material date")
    try:
        date.fromisoformat(stamp)
    except ValueError as exc:
        raise ValueError("Published bank snapshot date is invalid") from exc
    if not all(isinstance(k, str) and isinstance(v, dict)
               for k, v in bank["codes"].items()):
        raise ValueError("Published bank codes are malformed")
    return bank


def date_for_code(current: dict, published: dict | None, code: str) -> str:
    """Preserve published date iff the exact public code entry is unchanged."""
    current_date = current.get("effective_date", "")
    if (published is not None and
            code in current.get("codes", {}) and
            code in published["codes"] and
            current["codes"][code] == published["codes"][code]):
        return published["effective_date"]
    return current_date
