"""Carga y validación del registro de fuentes (DATA_SOURCES_REGISTRY.yaml)."""
from functools import lru_cache

import yaml

from .paths import REGISTRY_FILE

LICENSE_STATES = {"VERIFIED_PUBLIC_USE", "ATTRIBUTION_REQUIRED", "VERIFIED_INTERNAL_ONLY", "UNKNOWN", "RESTRICTED", "EXCLUDED"}
PUBLISHABLE = {"VERIFIED_PUBLIC_USE", "ATTRIBUTION_REQUIRED"}


@lru_cache(maxsize=4)
def load(path: str = REGISTRY_FILE) -> dict:
    with open(path, encoding="utf-8") as f:
        reg = yaml.safe_load(f)
    defaults = reg.get("defaults", {})
    out = {}
    for s in reg["sources"]:
        if s["id"] in out:
            raise ValueError(f"fuente duplicada: {s['id']}")
        if s.get("license") not in LICENSE_STATES:
            raise ValueError(f"{s['id']}: estado de licencia desconocido {s.get('license')!r}")
        if s.get("publish") and s["license"] not in PUBLISHABLE:
            raise ValueError(f"{s['id']}: publish=true no permitido con licencia {s['license']}")
        merged = {**defaults, **s}
        out[s["id"]] = merged
    return {"meta": {k: v for k, v in reg.items() if k != "sources"}, "sources": out}


def get(source_id: str) -> dict:
    return load()["sources"][source_id]


def all_sources() -> dict:
    return load()["sources"]


def is_publishable(source_id: str) -> bool:
    s = get(source_id)
    return bool(s.get("publish")) and s["license"] in PUBLISHABLE
