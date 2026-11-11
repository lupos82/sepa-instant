"""Per-bank-code source dates, never global directory observation churn.

Production audit only: a historical public catalogue may supply the source date
for UNCHANGED codes, but the real, current catalogue always provides bank data.
The caller must separately authenticate the historical bytes against the active
FTPS manifest before any release is planned or approved.
"""
from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import re

_COUNTRY = re.compile(r"^[A-Z]{2}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_CATALOG_BYTES = 1_000_000
MAX_LEDGER_BYTES = 350_000
LEDGER = 'bank-page-dates.json'


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


def valid_date(value: object) -> bool:
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def load_previous_dates(path: Path, baseline_root: Path,
                        published_banks: dict[str, dict]) -> dict[str, dict[str, str]]:
    """Verify history belongs to the EXACT old bank files (already FTPS-hashed).

    Missing ledger is permitted only for the inaugural rollout. Once the
    provider's live manifest records it, the caller MUST supply it or block.
    """
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_LEDGER_BYTES:
        raise ValueError("Missing, linked or oversized published bank-date ledger")
    try:
        obj = json.loads(path.read_bytes())
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError("Invalid published bank-date ledger JSON") from exc
    if (not isinstance(obj, dict) or set(obj) !=
            {"schema", "catalog_hashes", "dates"} or obj["schema"] != 1 or
            not isinstance(obj["catalog_hashes"], dict) or
            not isinstance(obj["dates"], dict) or
            set(obj["catalog_hashes"]) != set(published_banks) or
            set(obj["dates"]) != set(published_banks)):
        raise ValueError("Bank-date ledger country/schema mismatch")
    for country, published in published_banks.items():
        original_bytes = (baseline_root / (country + ".json")).read_bytes()
        if obj["catalog_hashes"][country] != sha256(original_bytes).hexdigest():
            raise ValueError("Bank-date ledger references a different published catalog")
        dates = obj["dates"][country]
        if (not isinstance(dates, dict) or set(dates) != set(published["codes"]) or
                not all(valid_date(value) for value in dates.values())):
            raise ValueError("Bank-date ledger entries are incomplete or invalid")
    return obj["dates"]


def date_for_code(current: dict, published: dict | None, code: str,
                  prior_dates: dict[str, str] | None = None) -> str:
    """Carry forward last material date only if the FULL bank entry matches."""
    current_date = current.get("effective_date", "")
    if (published is not None and
            code in current.get("codes", {}) and
            code in published["codes"] and
            current["codes"][code] == published["codes"][code]):
        return (prior_dates[code] if prior_dates is not None
                else published["effective_date"])
    return current_date
