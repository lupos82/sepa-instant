"""GLEIF: fichero de relación BIC-LEI (SWIFT/GLEIF) y API de registros LEI (CC0)."""
import csv
import io
import json
import time
import urllib.parse
import zipfile

from .. import countries
from ..http import fetch
from ..util import norm_bic, norm_lei
from .base import Connector


def _sepa_bic_countries():
    cc = set()
    for c in countries.countries():
        cc.add(c["iban_prefix"])
        cc.add(c["iso"])
        for t in c.get("territories", []):
            if len(t["iso"]) == 2:
                cc.add(t["iso"])
    return cc


class GLEIFBicLeiConnector(Connector):
    kind = "bic_lei"

    def download(self, state):
        idx = fetch(self.cfg["url"], retries=int(self.cfg.get("retries", 3)), accept="application/vnd.api+json")
        files = json.loads(idx.content.decode("utf-8"))["data"]
        valid = [f for f in files if f.get("attributes", {}).get("valid", True)]
        latest = max(valid, key=lambda f: f["attributes"].get("uploadedAt", ""))
        self._date = latest["attributes"].get("uploadedAt", "")[:10]
        return fetch(latest["attributes"]["downloadLink"], etag=state.get("etag", ""),
                     last_modified=state.get("last_modified", ""), retries=int(self.cfg.get("retries", 3)))

    def parse(self, raw: bytes, meta) -> list:
        cc = _sepa_bic_countries()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
            with z.open(name) as fp:
                reader = csv.DictReader(io.TextIOWrapper(fp, encoding="utf-8-sig"))
                out = []
                for row in reader:
                    bic = norm_bic(row.get("BIC", ""))
                    lei = norm_lei(row.get("LEI", ""))
                    if bic and lei and bic[4:6] in cc:
                        out.append({"kind": "bic_lei", "bic": bic, "lei": lei, "src": self.source_id})
        out.sort(key=lambda r: (r["bic"], r["lei"]))
        if not out:
            raise ValueError("fichero BIC-LEI sin filas SEPA")
        return out

    def effective_date(self, raw, meta) -> str:
        return getattr(self, "_date", "")


class GLEIFLeiConnector(Connector):
    """Resuelve nombres legales de una lista de LEI (lotes de 100, 1 petición/segundo)."""
    kind = "lei"
    BATCH = 100

    def run_for(self, leis, previous: dict, max_age_days: int = 30):
        from ..util import today
        from .base import RunResult
        res = RunResult(source_id=self.source_id, ok=True)
        known = {r["lei"]: r for r in previous}
        todo = sorted(l for l in leis if l not in known)
        out = dict(known)
        try:
            for i in range(0, len(todo), self.BATCH):
                batch = todo[i:i + self.BATCH]
                qs = urllib.parse.urlencode({"filter[lei]": ",".join(batch), "page[size]": self.BATCH})
                r = fetch(f"{self.cfg['url']}?{qs}", accept="application/vnd.api+json", retries=3)
                for rec in json.loads(r.content.decode("utf-8")).get("data", []):
                    ent = rec["attributes"]["entity"]
                    out[rec["id"]] = {"kind": "lei", "lei": rec["id"], "name": ent["legalName"]["name"].strip(),
                                      "country": (ent.get("legalAddress") or {}).get("country", ""),
                                      "status": ent.get("status", ""), "checked": today(), "src": self.source_id}
                time.sleep(1.0)
            res.changed = bool(todo)
        except Exception as e:  # noqa: BLE001
            res.ok, res.error = False, f"{type(e).__name__}: {e}"
        res.records = sorted(out.values(), key=lambda r: r["lei"])
        return res
