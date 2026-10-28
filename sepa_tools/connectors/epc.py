"""Registros de participantes del EPC (SCT, SCT Inst, SDD Core, SDD B2B)."""
import csv
import io
import re
from email.utils import parsedate_to_datetime

from .. import countries
from ..util import clean, decode_text, norm_bic, to_iso_date, today
from .base import Connector


def _norm_header(h):
    return re.sub(r"[^a-z]", "", h.lower())


class EPCConnector(Connector):
    kind = "sepa"

    def parse(self, raw: bytes, meta) -> list:
        text = decode_text(raw)
        first = text.splitlines()[0] if text else ""
        delim = ";" if first.count(";") > first.count(",") else ","
        reader = csv.reader(io.StringIO(text), delimiter=delim)
        header = [_norm_header(h) for h in next(reader)]
        if "bic" not in header or "participantname" not in header:
            raise ValueError(f"cabecera EPC inesperada: {header}")
        ix = {name: header.index(name) for name in header}

        def g(row, name):
            i = ix.get(name)
            return clean(row[i]) if i is not None and i < len(row) else ""

        scheme = self.cfg["scheme"]
        out = []
        seen = set()
        for row in reader:
            if not row or not any(row):
                continue
            bic = norm_bic(g(row, "bic"))
            if not bic:
                continue
            epc_country = g(row, "country").upper()
            iso = countries.epc_name_to_iso(epc_country) or bic[4:6]
            key = bic
            if key in seen:  # el EPC puede repetir un BIC; se conserva la primera fila
                continue
            seen.add(key)
            out.append({
                "kind": "sepa", "scheme": scheme, "bic": bic,
                "name": g(row, "participantname"), "address": g(row, "address"), "city": g(row, "city"),
                "country": iso, "epc_country": epc_country,
                "ready": to_iso_date(g(row, "readinessdate")), "leave": to_iso_date(g(row, "schemeleavingdate")),
                "options": g(row, "schemeoptions"), "src": self.source_id,
            })
        out.sort(key=lambda r: r["bic"])
        return out

    def effective_date(self, raw, meta) -> str:
        lm = getattr(meta, "last_modified", "")
        if lm:
            try:
                return parsedate_to_datetime(lm).date().isoformat()
            except (TypeError, ValueError):
                pass
        return today()
