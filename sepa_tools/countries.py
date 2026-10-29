"""Países y territorios SEPA (fuente: reference/sepa_countries.json)."""
import json
import os
from functools import lru_cache

from .paths import REFERENCE_DIR


@lru_cache(maxsize=1)
def load():
    with open(os.path.join(REFERENCE_DIR, "sepa_countries.json"), encoding="utf-8") as f:
        return json.load(f)


def countries():
    """Lista de países con IBAN propio (41 países SEPA + Gibraltar)."""
    return load()["countries"]


def sepa_41():
    return [c for c in countries() if c["group"] != "territory"]


def by_iso():
    return {c["iso"]: c for c in countries()}


def iban_prefixes():
    return {c["iban_prefix"] for c in countries()}


def epc_name_to_iso(name: str) -> str:
    m = load()["epc_country_names"]
    return m.get((name or "").strip().upper(), "")


def territory_parent():
    """ISO de territorio -> prefijo IBAN que utiliza (p. ej. JE -> GB)."""
    out = {}
    for c in countries():
        for t in c.get("territories", []):
            out[t["iso"]] = c["iban_prefix"]
    return out
