"""Directorios nacionales oficiales con licencia verificada: OeNB (AT), ČNB (CZ), Banco de España (ES)."""
import csv
import io
import re

from ..util import clean, decode_text, norm_bic, norm_lei, strip_accents, today, to_iso_date
from .base import Connector


def _sniff(text: str) -> str:
    first = next((l for l in text.splitlines() if l.strip()), "")
    counts = {d: first.count(d) for d in (";", ",", "\t")}
    return max(counts, key=counts.get)


def _key(h: str) -> str:
    return re.sub(r"[^a-z]", "", strip_accents(h).lower())


class OeNBConnector(Connector):
    kind = "bank_code"

    def parse(self, raw: bytes, meta) -> list:
        text = decode_text(raw, prefer=("utf-8-sig", "cp1252", "latin-1"))
        lines = text.splitlines()
        start = next((i for i, l in enumerate(lines) if l.startswith("Kennzeichen;")), None)
        if start is None:
            raise ValueError("cabecera 'Kennzeichen;' no encontrada en el fichero OeNB")
        self._date = ""
        for l in lines[:start]:
            m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", l)
            if m:
                self._date = f"{m[3]}-{m[2]}-{m[1]}"
        reader = csv.reader(io.StringIO("\n".join(lines[start:])), delimiter=";")
        header = [_key(h) for h in next(reader)]
        need = {"bankleitzahl", "bankenname", "swiftcode"}
        if not need.issubset(header):
            raise ValueError(f"columnas OeNB inesperadas: {header}")
        ix = {h: i for i, h in enumerate(header)}

        def g(row, k):
            i = ix.get(k)
            return clean(row[i]) if i is not None and i < len(row) else ""

        out = []
        for row in reader:
            if not row or not any(row):
                continue
            code = re.sub(r"\D", "", g(row, "bankleitzahl"))
            if not code:
                continue
            out.append({
                "kind": "bank_code", "country": "AT", "code": code.zfill(5),
                "primary": g(row, "kennzeichen").lower().startswith("haupt") or g(row, "institutsart") == "KI",
                "name": g(row, "bankenname"), "city": g(row, "ort"), "bic": norm_bic(g(row, "swiftcode")),
                "lei": norm_lei(g(row, "lei")), "founded": to_iso_date(g(row, "grundungsdatum")),
                "relation": "OFFICIAL_LIST", "src": self.source_id,
            })
        return out

    def effective_date(self, raw, meta) -> str:
        return getattr(self, "_date", "") or today()


class CNBConnector(Connector):
    kind = "bank_code"

    def parse(self, raw: bytes, meta) -> list:
        text = decode_text(raw, prefer=("utf-8-sig", "cp1250", "latin-1"))
        reader = csv.reader(io.StringIO(text), delimiter=_sniff(text))
        rows = [r for r in reader if r and any(c.strip() for c in r)]
        if not rows:
            raise ValueError("fichero ČNB vacío")
        if not re.fullmatch(r"\d{4}", rows[0][0].strip()):  # primera fila = cabecera
            rows = rows[1:]
        out = []
        for r in rows:
            code = r[0].strip()
            if not re.fullmatch(r"\d{4}", code):
                continue
            out.append({"kind": "bank_code", "country": "CZ", "code": code, "primary": True,
                        "name": clean(r[1] if len(r) > 1 else ""), "bic": norm_bic(r[2] if len(r) > 2 else ""),
                        "relation": "OFFICIAL_LIST", "src": self.source_id})
        return out

    def effective_date(self, raw, meta) -> str:
        return today()


class BdEMFIConnector(Connector):
    """Lista de IFM de España del Banco de España.

    Se aceptan entidades de crédito y el banco central con "Código supervisor" de 4 dígitos.
    """
    kind = "bank_code"
    INCLUDE = ("credito", "banco central", "central bank", "credit institution")

    def parse(self, raw: bytes, meta) -> list:
        text = decode_text(raw, prefer=("utf-8-sig", "utf-16", "cp1252", "latin-1"))
        reader = csv.reader(io.StringIO(text), delimiter=_sniff(text))
        header = [_key(h) for h in next(reader)]
        alias = {"codigoeuropeo": "riad", "europeancode": "riad", "lei": "lei", "nombre": "name", "name": "name",
                 "categoria": "category", "category": "category", "direccion": "address", "address": "address",
                 "entidadmatriz": "parent", "parententity": "parent", "codigosupervisor": "code",
                 "supervisorcode": "code"}
        cols = {alias[h]: i for i, h in enumerate(header) if h in alias}
        if "code" not in cols or "name" not in cols:
            raise ValueError(f"columnas BdE inesperadas: {header}")

        def g(row, k):
            i = cols.get(k)
            return clean(row[i]) if i is not None and i < len(row) else ""

        out = []
        for row in reader:
            if not row or not any(row):
                continue
            code = g(row, "code")
            cat = strip_accents(g(row, "category")).lower()
            if not re.fullmatch(r"\d{4}", code) or not any(k in cat for k in self.INCLUDE):
                continue
            riad = g(row, "riad").upper()
            out.append({
                "kind": "bank_code", "country": "ES", "code": code, "primary": True, "name": g(row, "name"),
                "legal_name": g(row, "name"), "lei": norm_lei(g(row, "lei")), "category": g(row, "category"),
                "address": g(row, "address"), "riad": riad, "parent_riad": g(row, "parent").upper(),
                "riad_matches_code": riad == f"ES{code}",
                "relation": "OFFICIAL_LIST", "src": self.source_id,
            })
        if not out:
            raise ValueError("ninguna entidad de crédito con código de 4 dígitos")
        return out

    def effective_date(self, raw, meta) -> str:
        return today()
