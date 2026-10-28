"""Directorios bancarios incluidos en el paquete schwifty (ficheros generated_*.json).

Solo se leen ficheros "generated_" cuya fuente original es oficial y está declarada en el
registro (bundle_files). Los ficheros "manual_" y los de procedencia no oficial no se usan.
La lectura se hace sobre los datos del paquete instalado (importlib.resources), sin
funciones internas.
"""
import json
from importlib import resources

from ..ibanspec import schwifty_version
from ..util import clean, norm_bic
from .base import Connector, RunResult


def read_bundle(filename: str) -> list:
    path = resources.files("schwifty").joinpath("bank_registry", filename)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):  # formato v2: {"entries": [{..., "bank_codes": [...]}]}
        rows = []
        for e in data.get("entries", []):
            for code in e.get("bank_codes", []):
                rows.append({**e, "bank_code": code})
        return rows
    return data


class SchwiftyBundleConnector(Connector):
    kind = "bank_code"

    def run(self, state: dict, raw_override=None) -> RunResult:
        res = RunResult(source_id=self.source_id, ok=False, version=f"schwifty {schwifty_version()}")
        try:
            out = []
            for fn in self.cfg.get("bundle_files", []):
                for r in read_bundle(fn):
                    code = clean(r.get("bank_code"))
                    if not code:
                        continue
                    out.append({"kind": "bank_code", "country": r.get("country_code", "").upper(), "code": code,
                                "primary": bool(r.get("primary")), "name": clean(r.get("name")),
                                "short_name": clean(r.get("short_name")), "bic": norm_bic(r.get("bic")),
                                "relation": "OFFICIAL_LIST_VIA_SCHWIFTY", "src": self.source_id})
            res.records = sorted(out, key=lambda x: (x["country"], x["code"], not x["primary"], x["bic"]))
            res.effective_date = res.version
            res.ok = True
            res.changed = state.get("version") != res.version
        except Exception as e:  # noqa: BLE001
            res.error = f"{type(e).__name__}: {e}"
        return res
