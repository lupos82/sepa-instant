"""BCE — lista diaria de instituciones financieras monetarias (MFI), CSV tabulado UTF-16."""
import csv
import gzip
import io
import re
from urllib.parse import urljoin

from ..http import fetch
from ..util import clean, decode_text, norm_lei
from .base import Connector


class ECBMFIConnector(Connector):
    kind = "mfi"

    def download(self, state):
        page = fetch(self.cfg["url"], retries=int(self.cfg.get("retries", 3)), accept="text/html")
        html = decode_text(page.content)
        links = re.findall(r'href="([^"]*mfi_csv_(\d{6})\.csv(?:\.gz)?)"', html)
        full = [(u, d) for u, d in links if "update" not in u]
        if not full:
            raise ValueError("no se encuentra el enlace mfi_csv_YYMMDD.csv en la página del BCE")
        gz = [x for x in full if x[0].endswith(".gz")]
        url, ymd = (gz or full)[0]
        self._date = f"20{ymd[:2]}-{ymd[2:4]}-{ymd[4:6]}"
        return fetch(urljoin(self.cfg["url"], url), etag=state.get("etag", ""),
                     last_modified=state.get("last_modified", ""), retries=int(self.cfg.get("retries", 3)))

    def parse(self, raw: bytes, meta) -> list:
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        text = decode_text(raw, prefer=("utf-16", "utf-8-sig", "latin-1"))
        reader = csv.reader(io.StringIO(text), delimiter="\t")
        header = [re.sub(r"[^A-Z]", "_", h.strip().upper()) for h in next(reader)]
        ix = {h: i for i, h in enumerate(header)}
        if "RIAD_CODE" not in ix or "NAME" not in ix:
            raise ValueError(f"columnas MFI inesperadas: {header[:8]}")

        def g(row, k):
            i = ix.get(k)
            return clean(row[i]) if i is not None and i < len(row) else ""

        out = []
        for row in reader:
            if not row or not any(row):
                continue
            cat = g(row, "CATEGORY").lower()
            if "credit" not in cat and "central bank" not in cat:  # solo entidades de crédito y bancos centrales
                continue
            out.append({
                "kind": "mfi", "riad": g(row, "RIAD_CODE").upper(), "lei": norm_lei(g(row, "LEI")),
                "country": g(row, "COUNTRY_OF_REGISTRATION").upper()[:2], "name": g(row, "NAME"),
                "category": g(row, "CATEGORY"), "city": g(row, "CITY"),
                "head_riad": g(row, "HEAD_RIAD_CODE").upper(), "head_lei": norm_lei(g(row, "HEAD_LEI")),
                "src": self.source_id,
            })
        return out

    def effective_date(self, raw, meta) -> str:
        return getattr(self, "_date", "")
