"""Clase base de los conectores.

Cada conector produce observaciones normalizadas (dicts) con procedencia:

  {"kind": "bank_code" | "sepa" | "bic" | "lei" | "mfi", ..., "src": <id fuente>}

El orquestador (sync.py) decide si las observaciones se aceptan (controles de calidad),
las guarda como instantánea y las pasa a la fusión (merge.py).
"""
from dataclasses import dataclass, field

from .. import sources
from ..http import fetch


@dataclass
class RunResult:
    source_id: str
    ok: bool
    changed: bool = False
    records: list = field(default_factory=list)
    version: str = ""            # versión o fecha efectiva de la fuente
    effective_date: str = ""
    fetched_url: str = ""
    sha256: str = ""
    etag: str = ""
    last_modified: str = ""
    error: str = ""
    warnings: list = field(default_factory=list)


class Connector:
    kind = "base"

    def __init__(self, source_id: str):
        self.source_id = source_id
        self.cfg = sources.get(source_id)

    # Por defecto: descarga la URL configurada y la parsea
    def download(self, state: dict):
        return fetch(self.cfg["url"], etag=state.get("etag", ""), last_modified=state.get("last_modified", ""),
                     retries=int(self.cfg.get("retries", 3)))

    def parse(self, raw: bytes, meta) -> list:
        raise NotImplementedError

    def effective_date(self, raw: bytes, meta) -> str:
        return ""

    def run(self, state: dict, raw_override: bytes = None) -> RunResult:
        res = RunResult(source_id=self.source_id, ok=False)
        try:
            if raw_override is not None:
                class _M:  # metadatos mínimos para pruebas / modo offline
                    url = "fixture"; sha256 = ""; etag = ""; last_modified = ""; not_modified = False
                meta = _M()
                raw = raw_override
            else:
                meta = self.download(state)
                if meta.not_modified:
                    res.ok, res.changed = True, False
                    res.etag, res.last_modified = meta.etag, meta.last_modified
                    return res
                raw = meta.content
                if state.get("sha256") and meta.sha256 == state.get("sha256"):
                    res.ok, res.changed, res.sha256 = True, False, meta.sha256
                    res.etag, res.last_modified = meta.etag, meta.last_modified
                    return res
            res.records = self.parse(raw, meta)
            res.effective_date = self.effective_date(raw, meta)
            res.fetched_url, res.sha256 = meta.url, getattr(meta, "sha256", "")
            res.etag, res.last_modified = getattr(meta, "etag", ""), getattr(meta, "last_modified", "")
            res.ok, res.changed = True, True
        except Exception as e:  # noqa: BLE001 — cualquier fallo de fuente se registra y no rompe el resto
            res.ok, res.error = False, f"{type(e).__name__}: {e}"
        return res
