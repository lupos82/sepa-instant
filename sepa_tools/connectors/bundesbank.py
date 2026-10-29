"""Deutsche Bundesbank — fichero de códigos bancarios (Bankleitzahlendatei), formato TXT.

Formato de registro (ancho fijo, 168 caracteres, latin-1), según la descripción oficial del
Bundesbank: BLZ(8) Merkmal(1) Bezeichnung(58) PLZ(5) Ort(35) Kurzbezeichnung(27) PAN(5)
BIC(11) Prüfzifferberechnungsmethode(2) Datensatz-Nr.(6) Änderungskennzeichen(1)
Hinweis auf Löschung(1) Nachfolge-BLZ(8).

La URL del fichero cambia cada trimestre: se localiza en la página pública de descargas.
No se usa el canal ExtraNet/NExt (requiere registro institucional).
"""
import re
from urllib.parse import urljoin

from ..http import fetch
from ..util import clean, decode_text, norm_bic
from .base import Connector

FIELDS = [("blz", 8), ("feature", 1), ("name", 58), ("postal", 5), ("city", 35), ("short_name", 27),
          ("pan", 5), ("bic", 11), ("check_method", 2), ("record_no", 6), ("change", 1), ("deletion", 1),
          ("successor", 8)]
RECORD_LEN = sum(n for _, n in FIELDS)


def parse_line(line: str) -> dict:
    rec, off = {}, 0
    for name, n in FIELDS:
        rec[name] = line[off:off + n].strip()
        off += n
    return rec


class BundesbankConnector(Connector):
    kind = "bank_code"

    def download(self, state):
        page = fetch(self.cfg["url"], retries=int(self.cfg.get("retries", 3)), accept="text/html")
        html = decode_text(page.content)
        m = re.search(r'href="([^"]*blz-aktuell-txt-data\.txt)"', html)
        if not m:
            raise ValueError("no se encuentra el enlace blz-aktuell-txt-data.txt en la página del Bundesbank")
        self._valid = ""
        v = re.search(r"(?:valid\s+(?:from\s+)?|g(?:ü|ue)ltig\s+(?:ab\s+|vom\s+)?)(\d{2})\.(\d{2})\.(\d{4})", html, re.I)
        if v:
            self._valid = f"{v[3]}-{v[2]}-{v[1]}"
        url = urljoin(self.cfg["url"], m.group(1))
        return fetch(url, etag=state.get("etag", ""), last_modified=state.get("last_modified", ""),
                     retries=int(self.cfg.get("retries", 3)))

    def parse(self, raw: bytes, meta) -> list:
        text = raw.decode("latin-1")
        out = []
        for line in text.splitlines():
            if not line.strip():
                continue
            if len(line.rstrip("\r\n")) < RECORD_LEN - 10:
                raise ValueError(f"línea con longitud inesperada ({len(line)}): formato cambiado")
            r = parse_line(line)
            if not re.fullmatch(r"\d{8}", r["blz"]):
                raise ValueError(f"BLZ no numérico: {r['blz']!r}")
            out.append({
                "kind": "bank_code", "country": "DE", "code": r["blz"], "primary": r["feature"] == "1",
                "name": clean(r["name"]), "short_name": clean(r["short_name"]), "postal": r["postal"],
                "city": clean(r["city"]), "bic": norm_bic(r["bic"]), "check_method": r["check_method"],
                "change": r["change"], "deleted": r["deletion"] == "1",
                "successor": r["successor"] if r["successor"] not in ("", "00000000") else "",
                "relation": "OFFICIAL_LIST", "src": self.source_id,
            })
        if not out:
            raise ValueError("fichero vacío")
        return out

    def effective_date(self, raw, meta) -> str:
        if getattr(self, "_valid", ""):
            return self._valid
        lm = getattr(meta, "last_modified", "") or ""
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(lm).date().isoformat() if lm else ""
        except (TypeError, ValueError):
            return ""
