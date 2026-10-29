"""Comprobaciones sobre los datos publicados reales (se ejecutan tras cada sincronización).

Además de controles estructurales, incluye "canarios": códigos públicamente conocidos cuya
resolución debe seguir siendo correcta. Un canario solo se evalúa si el país tiene directorio
publicado; si falla, la ejecución se marca como fallida y GitHub avisa por correo.
"""
import os
import re

from . import paths
from .util import read_json

CANARIES = [
    ("ES", "0049", r"santander"), ("ES", "0182", r"bilbao vizcaya|bbva"), ("ES", "2100", r"caixabank"),
    ("DE", "37040044", r"commerzbank"), ("DE", "10010010", r"postbank"), ("AT", "20111", r"erste"),
    ("CZ", "0800", r"spo[řr]itelna"), ("NL", "INGB", r"\bing\b"), ("NL", "ABNA", r"abn ?amro"),
    ("GB", "BARC", r"barclays"), ("IE", "AIBK", r"aib|allied irish"),
]
SEPA_CANARIES = ["CAIXESBBXXX", "COBADEFFXXX"]


def run() -> list:
    problems, notes = [], []
    specs = read_json(os.path.join(paths.DATA_DIR, "iban-specs.json"), {})
    if len(specs) < 42:
        problems.append(f"iban-specs.json tiene {len(specs)} países (se esperan 42)")
    sepa = read_json(os.path.join(paths.DATA_DIR, "sepa.json"), {})
    if len(sepa) < 1000:
        problems.append(f"sepa.json solo tiene {len(sepa)} BIC")
    for b in SEPA_CANARIES:
        if b not in sepa:
            problems.append(f"canario SEPA {b} ausente de sepa.json")
    for cc, code, pattern in CANARIES:
        d = read_json(os.path.join(paths.DATA_DIR, "banks", f"{cc}.json"), None)
        if not d:
            notes.append(f"{cc}: sin directorio publicado (canario {code} no evaluado)")
            continue
        e = d["codes"].get(code)
        if not e:
            problems.append(f"canario {cc} {code} no encontrado en banks/{cc}.json (fuente {d['source']})")
        elif not re.search(pattern, (e.get("n", "") + " " + e.get("ln", "")).lower()):
            problems.append(f"canario {cc} {code}: nombre inesperado {e.get('n')!r}")
    for n in notes:
        print(f"::notice::{n}")
    for p in problems:
        print(f"::error::{p}")
    print(f"selftest: {len(CANARIES) - len(notes)} canarios evaluados, {len(problems)} problemas")
    return problems
