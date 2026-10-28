#!/usr/bin/env python3
"""Genera el sitio estático de herramientas (ES/EN) a partir de data/v2.

Salida: <OUT_DIR>/tools/... (páginas), <OUT_DIR>/tools/data/v2/ (datos), <OUT_DIR>/tools/assets/.
Las páginas contienen todo su contenido en HTML (SEO); las herramientas usan el motor
web/engine/sepa-engine.js en el navegador.

Variables de entorno: PUBLIC_BASE (https://cryptopocket.io), CONTACT_URL, OUT_DIR (_site),
SEPA_TOOLS_ROOT (raíz del repositorio), NOINDEX=1 (copia de previsualización), EXTRA_HEAD_FILE / EXTRA_BODY_END_FILE (HTML opcional que la web
corporativa inyecta en <head> y al final de <body>: banner de cookies, analítica respetuosa…).
"""
import hashlib
import html
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import date, datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import site_content as SC  # noqa: E402

ROOT = os.environ.get("SEPA_TOOLS_ROOT") or os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data", "v2")
PUBLIC_BASE = os.environ.get("PUBLIC_BASE", "https://cryptopocket.io").rstrip("/")
CONTACT_URL = os.environ.get("CONTACT_URL", "https://cryptopocket.io/contact")
OUT = os.path.abspath(os.environ.get("OUT_DIR") or os.path.join(ROOT, "_site"))
PREFIX = "/tools"
LANGS = ("es", "en")
# Versión de los assets = hash de su contenido: la salida es determinista (mismos datos → mismos bytes),
# así el despliegue incremental (FTP/rsync) solo sube lo que cambia.
ASSET_V = hashlib.sha256(b"".join(open(os.path.join(d, n), "rb").read() for d, n in (
    (HERE, "site.css"), (HERE, "site.js"), (os.path.join(os.path.dirname(HERE), "web", "engine"), "sepa-engine.js")))).hexdigest()[:10]
E = html.escape
MONTHS = {"es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
          "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
PAGE_SIZE = 500


def jload(rel, default=None):
    try:
        with open(os.path.join(DATA, rel), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


SPECS = jload("iban-specs.json")
if not SPECS:
    sys.exit("ERROR: falta data/v2/iban-specs.json (ejecuta python -m sepa_tools sync)")
SEPA = jload("sepa.json", {})
META = jload("meta.json", {})
COV = jload("coverage.json", {"countries": {}, "totals": {}})
STATUS = jload("status.json", {}) or {}
CATALOG = {}
for f in sorted(os.listdir(os.path.join(DATA, "banks"))) if os.path.isdir(os.path.join(DATA, "banks")) else []:
    CATALOG[f[:-5]] = jload(f"banks/{f}")
TODAY = date.today().isoformat()
# Fecha del último cambio real de datos (no la hora de comprobación, que cambia cada día).
_DATES = [(v.get(k) or "")[:10] for v in (META.get("sources") or {}).values() for k in ("last_change", "effective_date")]
UPDATED = max([d for d in _DATES if re.match(r"\d{4}-\d{2}-\d{2}$", d)] or [TODAY])
# NOINDEX=1: copia de previsualización (p. ej. sepa.cryptopocket.io/tools) que no debe competir con la web corporativa.
ROBOTS = '<meta name="robots" content="noindex,follow">' if os.environ.get("NOINDEX") == "1" else ""
EXTRA_HEAD = open(os.environ["EXTRA_HEAD_FILE"], encoding="utf-8").read() if os.environ.get("EXTRA_HEAD_FILE") else ""
EXTRA_BODY_END = open(os.environ["EXTRA_BODY_END_FILE"], encoding="utf-8").read() if os.environ.get("EXTRA_BODY_END_FILE") else ""


def fmt_date(d, lang):
    if not d or not re.match(r"\d{4}-\d{2}-\d{2}", d):
        return "–"
    y, m, dd = int(d[:4]), int(d[5:7]), int(d[8:10])
    return f"{dd} de {MONTHS['es'][m - 1]} de {y}" if lang == "es" else f"{dd} {MONTHS['en'][m - 1]} {y}"


def fmt_n(n, lang):
    s = f"{n:,}"
    return s.replace(",", ".") if lang == "es" else s


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def cname(prefix, lang):
    return SPECS[prefix]["name"][lang] if prefix in SPECS else prefix


def code_type(prefix, lang):
    ct = SPECS[prefix].get("code_type") or {}
    return ct.get(lang) or ct.get("en") or ""


# ---- participantes EPC -------------------------------------------------------
def inst_status(p):
    x = p["s"].get("SCT_INST")
    return x[2] if x else "NOT_REGISTERED"


def iso_of(bic, p):
    return p.get("cc") or bic[4:6]


BYCC = {}
for bic, p in SEPA.items():
    BYCC.setdefault(iso_of(bic, p), []).append((bic, p))
for v in BYCC.values():
    v.sort(key=lambda bp: (bp[1]["n"].upper(), bp[0]))
INST_BYCC = {cc: [(b, p) for b, p in lst if inst_status(p) in ("REGISTERED", "FUTURE")] for cc, lst in BYCC.items()}
INST_BYCC = {cc: v for cc, v in INST_BYCC.items() if v}
N_INST = sum(len(v) for v in INST_BYCC.values())
N_INST_COUNTRIES = len(INST_BYCC)
LATEST = max((p["s"]["SCT_INST"][0] for p in SEPA.values() if inst_status(p) == "REGISTERED" and p["s"]["SCT_INST"][0]), default="")


def country_name_any(cc, lang):
    if cc in SPECS:
        return cname(cc, lang)
    for p, s in SPECS.items():
        for t in s.get("territories", []):
            if t["iso"] == cc:
                return t[lang]
    return cc


# ---- rutas ---------------------------------------------------------------------
def P(lang, key, *rest):
    parts = [PREFIX, lang] + ([SC.SLUGS[lang][key]] if key else []) + [x for x in rest if x]
    return "/".join(parts) + "/"


def p_hub(l): return f"{PREFIX}/{l}/"
def p_identify(l): return P(l, "identify")
def p_code(l): return P(l, "code")
def p_code_country(l, pre, page=1): return P(l, "code", slugify(cname(pre, l)), str(page) if page > 1 else "")
def p_code_item(l, pre, code): return P(l, "code", slugify(cname(pre, l)), code.lower())
def p_sepa(l): return P(l, "sepa")
def p_country(l, cc): return P(l, "sepa", slugify(country_name_any(cc, l)))
def p_bank(l, bic): return P(l, "bank", bic.lower())
def p_iban(l): return P(l, "iban")
def p_iban_c(l, pre): return P(l, "iban", slugify(cname(pre, l)))
def p_bic(l): return P(l, "bic")
def p_guides(l): return P(l, "guides")
def p_guide(l, g): return P(l, "guides", g["slug"][l])
def p_sources(l): return P(l, "sources")


CODE_PAGES = {pre: d for pre, d in CATALOG.items() if d["relation"] == "OFFICIAL_LIST"}
GUIDE = {g["key"]: g for g in SC.GUIDES}

# ---- textos de la interfaz (JS) -------------------------------------------------
JS = {
    "es": {
        "loading": "Comprobando…", "err_load_h": "No se han podido cargar los datos", "err_load": "Recarga la página en unos minutos.",
        "iban_ok": "IBAN válido", "iban_ok_p": "Formato, longitud y dígitos de control correctos. Un IBAN válido no garantiza que la cuenta exista.",
        "iban_bad": "IBAN no válido", "country": "País", "checksum": "Dígitos de control", "national": "Control nacional",
        "ok": "Correctos", "wrong": "Incorrectos", "nat_valid": "Correcto", "nat_invalid": "Incorrecto", "nat_na": "No aplicable o no disponible para este país",
        "err": {"FORMAT": "Un IBAN empieza por el código del país (2 letras) y 2 dígitos de control.", "INCOMPLETE": "El IBAN está incompleto: en este país tiene {n} caracteres.",
                "WRONG_LENGTH": "Longitud incorrecta: en este país el IBAN tiene {n} caracteres.", "WRONG_STRUCTURE": "La estructura no corresponde al formato de este país.",
                "CHECKSUM": "Los dígitos de control no cuadran: revisa que no falte ni sobre ningún carácter.", "NATIONAL_CHECK": "El control nacional de la cuenta no es correcto.",
                "UNSUPPORTED_COUNTRY": "Ese código de país no pertenece a la zona SEPA o no usa IBAN.", "INVALID_CHARACTERS": "El IBAN solo puede contener letras y números.",
                "TOO_LONG": "El texto es demasiado largo para ser un IBAN."},
        "bank_h": "Banco", "code_type": "Tipo de código", "bank_code": "Código bancario", "branch_code": "Código de oficina", "city": "Ciudad", "status": "Estado",
        "bank_identified": "Banco identificado", "bank_ambiguous": "Varias entidades posibles", "bic_confirmed": "BIC confirmado por la fuente oficial",
        "bic_candidate": "BIC candidato (no confirmado)", "bic_none": "Sin BIC verificado", "deletion": "Código con baja programada", "more_code": "Ficha del código bancario",
        "bank_not_found": "Banco no encontrado en nuestra base", "bank_not_found_p": "El código no figura en el directorio oficial que usamos. No significa que el banco no exista: puede ser una entidad de pago, de dinero electrónico o un código reciente.",
        "dir_none": "Directorio bancario no disponible para este país", "dir_none_p": "No hemos encontrado un directorio oficial con licencia de reutilización verificada. Mostramos el código bancario extraído del IBAN.",
        "dir_pending": "Directorio pendiente de verificación de licencia", "dir_pending_p": "Existe un directorio oficial, pero aún no hemos verificado sus condiciones de reutilización, así que no lo mostramos.",
        "sepa_no_bic": "Sin BIC verificado no podemos consultar los registros SEPA del EPC para este banco.",
        "reg": "Adherido", "future": "Adhesión futura", "left": "Baja del esquema", "notreg": "No figura", "unknown": "Desconocido", "since": "desde", "from": "a partir del", "left_on": "baja el",
        "inst_yes": "Adherido a SEPA Instant", "inst_yes_p": "Figura en el registro SCT Inst del EPC. La adhesión no garantiza que cada transferencia se acepte.",
        "inst_future": "Todavía no acepta SEPA Instant", "inst_future_p": "Se incorpora al esquema el {d}.",
        "inst_no": "No figura en el registro SEPA Instant", "inst_no_p": "Puede participar a través de otra entidad. En la zona euro los bancos deben recibir pagos inmediatos desde enero de 2025: confírmalo antes de enviar.",
        "info_h": "Información", "bank_src": "Fuente bancaria", "epc_src": "Fuente SEPA: registros de participantes del EPC", "checked": "Datos comprobados el",
        "warn": {"REACHABILITY_NOT_GUARANTEED": "Estar inscrito en un esquema EPC no garantiza la entrega de una transferencia concreta.",
                 "BIC_CANDIDATE_NOT_CONFIRMED": "El BIC se ha obtenido por el LEI de la entidad (fichero GLEIF/SWIFT): es un candidato, no una relación confirmada por la fuente oficial.",
                 "BIC_PREFIX_CONVENTION": "En este país el código bancario coincide con las 4 primeras letras del BIC; la entidad se deduce de los BIC registrados.",
                 "CODE_DELETION_SCHEDULED": "El banco ha comunicado la baja de este código; se indica el código sucesor si existe.",
                 "DATA_STALE": "Los datos llevan más de 3 días sin comprobarse.", "DIRECTORY_PARTIAL": "El directorio de este país no incluye todas las entidades (por ejemplo, entidades de pago).",
                 "IBAN_VALID_NOT_ACCOUNT_EXISTENCE": "Un IBAN válido no confirma que la cuenta exista ni quién es su titular.",
                 "NATIONAL_CHECK_NOT_AVAILABLE": "Para este país no se aplica un control nacional adicional.", "SOURCE_CONFLICT": "Las fuentes no coinciden en el BIC de este código; se muestra el de la fuente prioritaria.",
                 "FUTURE_PARTICIPATION": "La adhesión a SEPA Instant tiene fecha futura.", "SEPA_MATCH_HEAD_OFFICE": "La participación SEPA se ha encontrado por el BIC de la oficina principal.",
                 "FALLBACK_SOURCE": "Datos de respaldo: copia del directorio oficial incluida en schwifty, mientras se recupera la descarga directa.",
                 "IDENTIFICATION_FROM_INVALID_IBAN": "El IBAN no es válido: el banco se muestra solo a título orientativo.", "TEST_BIC": "Es un BIC de pruebas (segundo carácter de localidad '0')."},
        "bic_bad": "BIC no válido", "bic_bad_p": "Un BIC tiene 8 u 11 caracteres: 4 de entidad, 2 de país, 2 de localidad y 3 opcionales de oficina.",
        "bic_ok": "Formato de BIC correcto", "bic_ok_p": "La estructura del código es válida.", "bank": "Entidad", "not_identified": "No identificada en nuestras fuentes",
        "bic_inst": "Código de entidad", "bic_loc": "Localidad", "bic_test": "BIC de pruebas", "bic_branch": "Oficina", "bic_head": "oficina principal", "nat_ids": "Códigos nacionales",
        "none": "Sin resultados", "none_p": "Prueba con otra parte del nombre o con el BIC.", "results": "{n} de {t} resultados",
        "code_bad": "Código con formato incorrecto", "code_bad_p": "En este país el código bancario tiene {n} caracteres.",
    },
    "en": {
        "loading": "Checking…", "err_load_h": "The data could not be loaded", "err_load": "Please reload the page in a few minutes.",
        "iban_ok": "Valid IBAN", "iban_ok_p": "Format, length and check digits are correct. A valid IBAN does not guarantee the account exists.",
        "iban_bad": "Invalid IBAN", "country": "Country", "checksum": "Check digits", "national": "National check",
        "ok": "Correct", "wrong": "Incorrect", "nat_valid": "Correct", "nat_invalid": "Incorrect", "nat_na": "Not applicable or not available for this country",
        "err": {"FORMAT": "An IBAN starts with the country code (2 letters) and 2 check digits.", "INCOMPLETE": "The IBAN is incomplete: in this country it has {n} characters.",
                "WRONG_LENGTH": "Wrong length: in this country the IBAN has {n} characters.", "WRONG_STRUCTURE": "The structure does not match this country's format.",
                "CHECKSUM": "The check digits do not match: make sure no character is missing or extra.", "NATIONAL_CHECK": "The national account check is not correct.",
                "UNSUPPORTED_COUNTRY": "That country code is not in SEPA or does not use IBAN.", "INVALID_CHARACTERS": "An IBAN can only contain letters and digits.",
                "TOO_LONG": "The text is too long to be an IBAN."},
        "bank_h": "Bank", "code_type": "Code type", "bank_code": "Bank code", "branch_code": "Branch code", "city": "City", "status": "Status",
        "bank_identified": "Bank identified", "bank_ambiguous": "Several possible institutions", "bic_confirmed": "BIC confirmed by the official source",
        "bic_candidate": "Candidate BIC (not confirmed)", "bic_none": "No verified BIC", "deletion": "Code scheduled for deletion", "more_code": "Bank code details",
        "bank_not_found": "Bank not found in our database", "bank_not_found_p": "The code is not in the official directory we use. This does not mean the bank does not exist: it may be a payment or e-money institution or a new code.",
        "dir_none": "No bank directory available for this country", "dir_none_p": "We have not found an official directory with verified reuse terms. We show the bank code extracted from the IBAN.",
        "dir_pending": "Directory pending licence verification", "dir_pending_p": "An official directory exists, but we have not yet verified its reuse terms, so we do not show it.",
        "sepa_no_bic": "Without a verified BIC we cannot check the EPC SEPA registers for this bank.",
        "reg": "Registered", "future": "Future participation", "left": "Left the scheme", "notreg": "Not listed", "unknown": "Unknown", "since": "since", "from": "from", "left_on": "left on",
        "inst_yes": "Registered for SEPA Instant", "inst_yes_p": "Listed in the EPC SCT Inst register. Registration does not guarantee every transfer will be accepted.",
        "inst_future": "Not accepting SEPA Instant yet", "inst_future_p": "Joins the scheme on {d}.",
        "inst_no": "Not listed in the SEPA Instant register", "inst_no_p": "It may participate through another institution. In the euro area banks must receive instant payments since January 2025: confirm before sending.",
        "info_h": "Information", "bank_src": "Bank source", "epc_src": "SEPA source: EPC registers of participants", "checked": "Data checked on",
        "warn": {"REACHABILITY_NOT_GUARANTEED": "Being registered in an EPC scheme does not guarantee delivery of a specific transfer.",
                 "BIC_CANDIDATE_NOT_CONFIRMED": "The BIC was obtained via the institution's LEI (GLEIF/SWIFT file): it is a candidate, not a link confirmed by the official source.",
                 "BIC_PREFIX_CONVENTION": "In this country the bank code equals the first 4 letters of the BIC; the institution is derived from registered BICs.",
                 "CODE_DELETION_SCHEDULED": "The bank has announced this code will be deleted; the successor code is shown where available.",
                 "DATA_STALE": "The data has not been checked for more than 3 days.", "DIRECTORY_PARTIAL": "This country's directory does not include every institution (for example payment institutions).",
                 "IBAN_VALID_NOT_ACCOUNT_EXISTENCE": "A valid IBAN does not confirm that the account exists or who holds it.",
                 "NATIONAL_CHECK_NOT_AVAILABLE": "No additional national check applies to this country.", "SOURCE_CONFLICT": "Sources disagree on this code's BIC; the priority source is shown.",
                 "FUTURE_PARTICIPATION": "SEPA Instant participation has a future date.", "SEPA_MATCH_HEAD_OFFICE": "SEPA participation was found via the head office BIC.",
                 "FALLBACK_SOURCE": "Fallback data: copy of the official directory bundled in schwifty while the direct download is restored.",
                 "IDENTIFICATION_FROM_INVALID_IBAN": "The IBAN is not valid: the bank is shown for guidance only.", "TEST_BIC": "This is a test BIC (second location character '0')."},
        "bic_bad": "Invalid BIC", "bic_bad_p": "A BIC has 8 or 11 characters: 4 for the institution, 2 for the country, 2 for the location and an optional 3 for the branch.",
        "bic_ok": "Valid BIC format", "bic_ok_p": "The code structure is valid.", "bank": "Institution", "not_identified": "Not identified in our sources",
        "bic_inst": "Institution code", "bic_loc": "Location", "bic_test": "test BIC", "bic_branch": "Branch", "bic_head": "head office", "nat_ids": "National codes",
        "none": "No results", "none_p": "Try another part of the name or the BIC.", "results": "{n} of {t} results",
        "code_bad": "Wrong code format", "code_bad_p": "In this country the bank code has {n} characters.",
    },
}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">')
SITEMAP = []


def nav_items(lang):
    t = SC.T[lang]
    return [("identify", p_identify(lang), t["nav_identify"]), ("iban", p_iban(lang), t["nav_iban"]), ("code", p_code(lang), t["nav_code"]),
            ("bic", p_bic(lang), t["nav_bic"]), ("sepa", p_sepa(lang), t["nav_sepa"]), ("guides", p_guides(lang), t["nav_guides"])]


def page(lang, path, title, desc, body, alts, crumbs=None, schema=None, nav=None, tool=False):
    t = SC.T[lang]
    other = "en" if lang == "es" else "es"
    alt_links = "".join(f'<link rel="alternate" hreflang="{l}" href="{PUBLIC_BASE}{p}">' for l, p in alts.items())
    alt_links += f'<link rel="alternate" hreflang="x-default" href="{PUBLIC_BASE}{alts.get("en", path)}">'
    cur = ' aria-current="page"'
    nav_html = "".join(f'<a href="{u}"{cur if k == nav else ""}>{E(lbl)}</a>' for k, u, lbl in nav_items(lang))
    sch = list(schema or [])
    crumb_html = ""
    if crumbs:
        items = [(t["home"], p_hub(lang))] + crumbs
        crumb_html = '<nav class="crumbs wrap" aria-label="breadcrumb"><ol>' + "".join(
            f'<li><a href="{u}">{E(n)}</a></li>' if i < len(items) - 1 else f'<li aria-current="page">{E(n)}</li>' for i, (n, u) in enumerate(items)) + "</ol></nav>"
        sch.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": PUBLIC_BASE + u} for i, (n, u) in enumerate(items)]})
    sch_html = "".join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace("</", "<\\/") + "</script>" for x in sch if x)
    cfg = ""
    if tool:
        names = {p: cname(p, lang) for p in SPECS}
        cfg = ('<script type="application/json" id="cfg">' + json.dumps({
            "lang": lang, "locale": t["locale"], "data": f"{PREFIX}/data/v2/", "bankBase": P(lang, "bank"), "codeBase": P(lang, "code"),
            "codeSlugs": {p: slugify(cname(p, lang)) for p in CODE_PAGES}, "s": JS[lang], "countryNames": names}, ensure_ascii=False).replace("</", "<\\/") + "</script>"
               f'<script src="{PREFIX}/assets/sepa-engine.js?v={ASSET_V}" defer></script><script src="{PREFIX}/assets/site.js?v={ASSET_V}" defer></script>')
    doc = f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
{ROBOTS}<link rel="canonical" href="{PUBLIC_BASE}{path}">
{alt_links}
<meta property="og:type" content="website"><meta property="og:site_name" content="Cryptopocket">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{PUBLIC_BASE}{path}"><meta property="og:image" content="https://cryptopocket.io/cryptopocket-og.png">
<meta property="og:locale" content="{'es_ES' if lang == 'es' else 'en_GB'}"><meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0d1526">
{FONTS}
<link rel="stylesheet" href="{PREFIX}/assets/site.css?v={ASSET_V}">
{sch_html}
{EXTRA_HEAD}
</head>
<body>
<a class="skip" href="#main">{'Saltar al contenido' if lang == 'es' else 'Skip to content'}</a>
<header class="top"><div class="wrap">
  <a class="logo" href="https://cryptopocket.io/">Cryptopocket <span>{E(t['brand_tag'])}</span></a>
  <nav class="nav" aria-label="Tools">{nav_html}</nav>
  <div class="top-r"><a class="lang" href="{alts.get(other, p_hub(other))}" hreflang="{other}" lang="{other}">{E(t['other_lang'])}</a><a class="btn-cta" href="{E(CONTACT_URL)}">{E(t['contact'])}</a></div>
</div></header>
{crumb_html}
<main class="wrap" id="main">
{body}
<aside class="cta"><div><h2>{E(t['cta_h'])}</h2><p>{E(t['cta_p'])}</p></div><a class="btn-cta" href="{E(CONTACT_URL)}">{E(t['cta_btn'])} →</a></aside>
</main>
<footer class="foot"><div class="wrap">
<p>{E(t['updated'])} {E(fmt_date(UPDATED, lang))}. {E(t['source_line'])} <a href="{p_sources(lang)}">{E(t['sources_link'])}</a>.</p>
<p>{E(t['disclaimer'])}</p>
<p>© {date.today().year} <a href="https://cryptopocket.io/">Cryptopocket</a> · {" · ".join(f'<a href="{u}">{E(lbl)}</a>' for _, u, lbl in nav_items(lang))}</p>
</div></footer>
{cfg}
{EXTRA_BODY_END}
</body>
</html>
"""
    out = os.path.join(OUT, path.strip("/"), "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    SITEMAP.append((path, alts))


def faq_html(qas, lang):
    if not qas:
        return "", None
    h = f'<section class="faq"><h2>{E(SC.T[lang]["faq"])}</h2>' + "".join(f"<details><summary>{E(q)}</summary><p>{a}</p></details>" for q, a in qas) + "</section>"
    return h, {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in qas]}


def web_app(name, url, desc):
    return {"@context": "https://schema.org", "@type": "WebApplication", "name": name, "url": PUBLIC_BASE + url, "description": desc,
            "applicationCategory": "FinanceApplication", "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
            "provider": {"@type": "Organization", "name": "Cryptopocket", "url": "https://cryptopocket.io"}}


def tool(kind, lang, label, placeholder, country="", hint=""):
    es = lang == "es"
    btn = "Comprobar" if es else "Check"
    clear = "Limpiar" if es else "Clear"
    sel = ""
    if kind == "code":
        opts = []
        for p in sorted(SPECS, key=lambda x: cname(x, lang)):
            s = SPECS[p]
            b = s["positions"].get("bank")
            if not b:
                continue
            n = b[1] - b[0]
            br = s["positions"].get("branch")
            hint_txt = (f"{code_type(p, lang)} · {n} {'caracteres' if es else 'characters'}") if not s["lookup_branch"] else (
                f"{code_type(p, lang)} · {n} + {br[1] - br[0]} {'caracteres' if es else 'characters'}")
            status = {"published": "", "pending_licence": " ⋯", "none": " –"}[s["directory"]]
            opts.append(f'<option value="{p}" data-len="{n + (br[1] - br[0] if s["lookup_branch"] and br else 0)}" data-ph="{"A" * n if s["bic_prefix_rule"] else "0" * n}" data-hint="{E(hint_txt)}">{E(cname(p, lang))}{status}</option>')
        sel = (f'<label for="c-{kind}">{"País" if es else "Country"}</label><select id="c-{kind}" class="sel">'
               f'<option value="">{"Elige un país" if es else "Choose a country"}</option>{"".join(opts)}</select>')
    data_country = f' data-country="{country}"' if country else ""
    return f"""<section class="panel tool" data-tool="{kind}"{data_country}>
<form role="search" autocomplete="off" novalidate>{sel}
<label for="q-{kind}">{E(label)}</label>
<div class="row"><input id="q-{kind}" type="text" data-private="true" data-hj-suppress data-clarity-mask="true" class="ph-no-capture" inputmode="text" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="64" placeholder="{E(placeholder)}"><button class="btn primary" type="submit">{btn}</button><button class="btn" type="button" data-clear>{clear}</button></div>
{f'<p class="hint code-hint">{E(hint)}</p>' if kind == "code" else ""}
</form>
<div class="out" aria-live="polite"></div>
</section>"""


def privacy(lang):
    return f'<p class="hint">🔒 {E(SC.T[lang]["privacy_note"])}</p>'


def status_badge(p, lang):
    es = lang == "es"
    d = SPECS[p]["directory"]
    return {"published": f'<span class="pill yes">{"Directorio publicado" if es else "Directory published"}</span>',
            "pending_licence": f'<span class="pill soon">{"Pendiente de licencia" if es else "Licence pending"}</span>',
            "none": f'<span class="pill">{"Sin directorio abierto" if es else "No open directory"}</span>'}[d]


# ============================================================================ páginas
def build_hub():
    for lang in LANGS:
        es = lang == "es"
        t = SC.T[lang]
        title = "Identificar banco por IBAN, validar IBAN y SEPA Instant | Cryptopocket" if es else "IBAN bank lookup, IBAN validator and SEPA Instant | Cryptopocket"
        desc = ("Herramientas gratuitas: saber de qué banco es un IBAN, validar IBAN, buscar código bancario y BIC, y comprobar SEPA Instant. Datos oficiales actualizados cada día."
                if es else "Free tools: find the bank of an IBAN, validate IBANs, look up bank codes and BICs, and check SEPA Instant. Official data updated daily.")
        cards = [(p_identify(lang), "Identificar banco por IBAN" if es else "IBAN bank lookup", "Saber de qué banco es un IBAN, su código y su BIC." if es else "Find which bank an IBAN belongs to, its code and BIC."),
                 (p_iban(lang), t["nav_iban"], "Comprueba formato y dígitos de control en 41 países SEPA." if es else "Check format and check digits in 41 SEPA countries."),
                 (p_code(lang), "Buscar banco por código" if es else "Bank code lookup", "Identifica una entidad por su código nacional sin el IBAN completo." if es else "Identify an institution by its national code without a full IBAN."),
                 (p_bic(lang), "Buscar BIC / SWIFT" if es else "BIC / SWIFT lookup", "Valida un BIC y consulta su participación SEPA." if es else "Validate a BIC and check its SEPA participation."),
                 (p_sepa(lang), "Comprobar SEPA Instant" if es else "SEPA Instant checker", "Bancos adheridos a transferencias inmediatas." if es else "Banks registered for instant transfers."),
                 (p_guides(lang), t["nav_guides"], "SEPA Instant, reglamento europeo y verificación del beneficiario." if es else "SEPA Instant, EU regulation and Verification of Payee.")]
        body = (f'<div class="hero"><h1>{"Herramientas bancarias SEPA" if es else "SEPA banking tools"}</h1><p class="lead">{E(desc)}</p></div>'
                + tool("identify", lang, "IBAN", "ES00 0000 0000 0000 0000 0000") + privacy(lang)
                + f'<h2>{"Herramientas" if es else "Tools"}</h2><div class="cards">' + "".join(f'<a class="card" href="{u}"><h3>{E(h)}</h3><p>{E(p)}</p></a>' for u, h, p in cards) + "</div>")
        page(lang, p_hub(lang), title, desc, body, {l: p_hub(l) for l in LANGS}, schema=[web_app("SEPA Tools", p_hub(lang), desc)], tool=True)
    # Sin código ni estilos en línea: compatible con una Content-Security-Policy estricta (integration/tools.htaccess).
    assets = os.path.join(OUT, "tools", "assets")
    os.makedirs(assets, exist_ok=True)
    with open(os.path.join(assets, "root.js"), "w", encoding="utf-8") as f:
        f.write(f"location.replace(/^es\\b/i.test(navigator.language||'')?'{p_hub('es')}':'{p_hub('en')}');\n")
    with open(os.path.join(assets, "root.css"), "w", encoding="utf-8") as f:
        f.write("body{font:16px system-ui,sans-serif;background:#0d1526;color:#fff;display:grid;place-items:center;min-height:100vh;margin:0;text-align:center}a{color:#c9a84c;margin:0 10px}\n")
    head = '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' + f'<link rel="stylesheet" href="{PREFIX}/assets/root.css">'
    links = f'<p><a href="{p_hub("es")}">Español</a> · <a href="{p_hub("en")}">English</a></p>'
    with open(os.path.join(OUT, "tools", "index.html"), "w", encoding="utf-8") as f:
        f.write(f"""<!doctype html><html lang="en"><head>{head}<title>Cryptopocket Tools</title>
<link rel="canonical" href="{PUBLIC_BASE}{p_hub('en')}"><link rel="alternate" hreflang="es" href="{PUBLIC_BASE}{p_hub('es')}"><link rel="alternate" hreflang="en" href="{PUBLIC_BASE}{p_hub('en')}">
<script src="{PREFIX}/assets/root.js"></script></head>
<body>{links}</body></html>""")
    with open(os.path.join(OUT, "tools", "404.html"), "w", encoding="utf-8") as f:
        f.write(f"""<!doctype html><html lang="es"><head>{head}<meta name="robots" content="noindex"><title>Página no encontrada · Page not found</title></head>
<body><div><h1>404</h1><p>Esta página no existe o el dato ya no figura en la fuente oficial.<br>This page does not exist or the record is no longer in the official source.</p>{links}</div></body></html>""")


def coverage_table(lang):
    es = lang == "es"
    rows = []
    for p in sorted(SPECS, key=lambda x: cname(x, lang)):
        s = SPECS[p]
        c = COV["countries"].get(p, {})
        n = c.get("codes")
        link = f'<a href="{p_iban_c(lang, p)}">{E(cname(p, lang))}</a>'
        rows.append(f'<tr><td>{link}</td><td class="mono">{p}</td><td class="num">{s["length"]}</td><td>{status_badge(p, lang)}</td><td class="num">{fmt_n(n, lang) if n else "–"}</td></tr>')
    return (f'<div class="tbl"><table><thead><tr><th>{"País" if es else "Country"}</th><th>IBAN</th><th>{"Longitud" if es else "Length"}</th>'
            f'<th>{"Identificación del banco" if es else "Bank identification"}</th><th>{"Códigos" if es else "Codes"}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def build_identify():
    for lang in LANGS:
        es = lang == "es"
        title = "Identificar banco por IBAN: ¿de qué banco es este IBAN? | Cryptopocket" if es else "IBAN bank lookup: which bank does this IBAN belong to? | Cryptopocket"
        desc = ("Introduce un IBAN y descubre a qué banco pertenece, su código bancario, el BIC cuando está verificado y si está adherido a SEPA Instant. Gratis y sin enviar el IBAN a ningún servidor."
                if es else "Enter an IBAN to find the bank it belongs to, its bank code, the BIC where verified and whether it is registered for SEPA Instant. Free, and the IBAN never leaves your browser.")
        tot = COV.get("totals", {})
        qas = [
            ("¿Cómo sé de qué banco es un IBAN?" if es else "How do I find which bank an IBAN belongs to?",
             (f'El IBAN contiene un código bancario cuya posición depende del país. Lo extraemos y lo buscamos en directorios oficiales. <a href="{p_guide(lang, GUIDE["identify"])}">Guía completa</a>.' if es else
              f'The IBAN contains a bank code whose position depends on the country. We extract it and look it up in official directories. <a href="{p_guide(lang, GUIDE["identify"])}">Full guide</a>.')),
            ("¿En qué países identifica el banco?" if es else "In which countries can the bank be identified?",
             (f"Validamos el formato en los 41 países SEPA. Identificamos el banco en {tot.get('countries_with_published_directory', 0)} países con directorio oficial o registro de BIC con licencia verificada; la tabla de abajo muestra el estado de cada país."
              if es else f"We validate the format in all 41 SEPA countries. We identify the bank in {tot.get('countries_with_published_directory', 0)} countries with an official directory or BIC register under verified licence terms; the table below shows each country's status.")),
            ("¿Se envía o guarda el IBAN?" if es else "Is the IBAN sent or stored?", E(SC.T[lang]["privacy_note"])),
            ("¿Un IBAN válido significa que la cuenta existe?" if es else "Does a valid IBAN mean the account exists?",
             "No. Solo el banco puede confirmar que la cuenta existe y quién es su titular." if es else "No. Only the bank can confirm that the account exists and who holds it."),
        ]
        faq, fs = faq_html(qas, lang)
        body = (f'<div class="hero"><h1>{"Identificar banco por IBAN" if es else "IBAN bank lookup"}</h1><p class="lead">{E(desc)}</p></div>'
                + tool("identify", lang, "IBAN", "ES00 0000 0000 0000 0000 0000") + privacy(lang)
                + f'<h2>{"Qué mostramos" if es else "What we show"}</h2><div class="prose"><ol>'
                + ("<li><strong>IBAN</strong>: país, estructura, dígitos de control y control nacional.</li><li><strong>Banco</strong>: código bancario, entidad y BIC cuando una fuente oficial los relaciona.</li><li><strong>SEPA</strong>: inscripción en SCT, SCT Inst y adeudos SEPA según los registros del EPC.</li><li><strong>Información</strong>: fuentes, fechas y limitaciones.</li>"
                   if es else "<li><strong>IBAN</strong>: country, structure, check digits and national check.</li><li><strong>Bank</strong>: bank code, institution and BIC where an official source links them.</li><li><strong>SEPA</strong>: registration in SCT, SCT Inst and SEPA direct debits according to EPC registers.</li><li><strong>Information</strong>: sources, dates and limitations.</li>")
                + "</ol></div>"
                + f'<h2>{"Cobertura por país" if es else "Coverage by country"}</h2>' + coverage_table(lang)
                + '<div class="prose">' + faq + "</div>")
        page(lang, p_identify(lang), title, desc, body, {l: p_identify(l) for l in LANGS}, crumbs=[(SC.T[lang]["nav_identify"], p_identify(lang))],
             schema=[web_app("IBAN bank lookup", p_identify(lang), desc), fs], nav="identify", tool=True)


def code_rows(lang, pre, codes, limit=None):
    es = lang == "es"
    out = []
    items = sorted(codes.items())
    for code, e in items[:limit] if limit else items:
        st = (f' <span class="pill soon">{"baja programada" if es else "deletion scheduled"}</span>' if e.get("st") == "DELETION_SCHEDULED" else "")
        name = E(e["n"])
        if pre in CODE_PAGES:
            name = f'<a href="{p_code_item(lang, pre, code)}">{name}</a>'
        bic = " ".join(E(b) for b in e.get("b", [])[:2])
        bst = "" if not e.get("b") else ("" if e.get("bs") == "CONFIRMED" else f' <span class="hint-inline">{"candidato" if es else "candidate"}</span>')
        out.append(f'<tr><td class="mono">{E(code)}</td><td>{name}{st}</td><td>{E(e.get("c", ""))}</td><td class="mono">{bic}{bst}</td></tr>')
    head = f'<tr><th>{"Código" if es else "Code"}</th><th>{"Entidad" if es else "Institution"}</th><th>{"Ciudad" if es else "City"}</th><th>BIC</th></tr>'
    return f'<div class="tbl"><table><thead>{head}</thead><tbody>{"".join(out)}</tbody></table></div>'


def source_note(lang, pre):
    d = CATALOG[pre]
    src = META.get("sources", {}).get(d["source"], {})
    es = lang == "es"
    date_txt = fmt_date(d.get("effective_date", ""), lang)
    return (f'<p class="hint">{"Fuente" if es else "Source"}: {E(src.get("institution") or d.get("attribution", ""))}'
            f'{(" · " + ("datos de" if es else "data as of") + " " + date_txt) if date_txt != "–" else ""}. {E(d.get("attribution", ""))}</p>')


def build_code_pages():
    for lang in LANGS:
        es = lang == "es"
        t = SC.T[lang]
        title = "Buscar banco por código bancario (BLZ, código de entidad, ABI…) | Cryptopocket" if es else "Bank code lookup (BLZ, sort codes, entity codes) | Cryptopocket"
        desc = ("Identifica un banco por su código nacional: código de entidad español, Bankleitzahl alemán, BLZ austriaco, código de banco checo y más. Sin necesidad del IBAN completo."
                if es else "Identify a bank by its national code: Spanish entity code, German Bankleitzahl, Austrian BLZ, Czech bank code and more. No full IBAN needed.")
        lst = "".join(f'<li><a href="{p_code_country(lang, p)}">{E(cname(p, lang))}</a> · {fmt_n(len(CATALOG[p]["codes"]), lang)} {"códigos" if es else "codes"}</li>'
                      for p in sorted(CODE_PAGES, key=lambda x: cname(x, lang)))
        body = (f'<div class="hero"><h1>{"Buscar banco por código" if es else "Bank code lookup"}</h1><p class="lead">{E(desc)}</p></div>'
                + tool("code", lang, "Código bancario" if es else "Bank code", "", hint=("Elige un país para ver el formato del código." if es else "Choose a country to see the code format."))
                + (f'<h2>{"Directorios de códigos" if es else "Code directories"}</h2><ul class="links col">{lst}</ul>' if lst else "")
                + f'<h2>{"Cobertura por país" if es else "Coverage by country"}</h2>' + coverage_table(lang))
        page(lang, p_code(lang), title, desc, body, {l: p_code(l) for l in LANGS}, crumbs=[(t["nav_code"], p_code(lang))],
             schema=[web_app("Bank code lookup", p_code(lang), desc)], nav="code", tool=True)

        for pre, d in CODE_PAGES.items():
            name = cname(pre, lang)
            ct = code_type(pre, lang)
            items = sorted(d["codes"].items())
            pages = max(1, (len(items) + PAGE_SIZE - 1) // PAGE_SIZE)
            for pg in range(1, pages + 1):
                chunk = dict(items[(pg - 1) * PAGE_SIZE: pg * PAGE_SIZE])
                ttl = (f"{ct} de {name}: lista de códigos bancarios" if es else f"{name} bank codes ({ct}): full list") + (f" ({pg}/{pages})" if pages > 1 else "") + " | Cryptopocket"
                ds = (f"Lista de {fmt_n(len(items), lang)} códigos bancarios de {name} ({ct}) con entidad, ciudad y BIC, según el directorio oficial." if es else
                      f"List of {fmt_n(len(items), lang)} {name} bank codes ({ct}) with institution, city and BIC, from the official directory.")
                pager = ""
                if pages > 1:
                    curp = ' aria-current="page"'
                    pager = '<nav class="pager">' + " ".join(
                        f'<a href="{p_code_country(lang, pre, i)}"{curp if i == pg else ""}>{i}</a>' for i in range(1, pages + 1)) + "</nav>"
                body = (f'<div class="hero"><h1>{E(ttl.split(" | ")[0])}</h1><p class="lead">{E(ds)}</p></div>'
                        + tool("code", lang, ct, "", country=pre) + source_note(lang, pre) + pager + code_rows(lang, pre, chunk) + pager)
                page(lang, p_code_country(lang, pre, pg), ttl, ds, body, {l: p_code_country(l, pre, pg) for l in LANGS},
                     crumbs=[(t["nav_code"], p_code(lang)), (name, p_code_country(lang, pre))], nav="code", tool=True)

            for code, e in items:
                bank = e["n"]
                bics = e.get("b", [])
                hit, sepa_bic = None, ""
                for b in bics:
                    for cand in (b, b[:8] + "XXX"):
                        if cand in SEPA:
                            hit, sepa_bic = SEPA[cand], cand
                            break
                    if hit:
                        break
                inst = inst_status(hit) if hit else "UNKNOWN"
                ttl = (f"{ct} {code}: {bank}" if es else f"{ct} {code}: {bank}") + " | Cryptopocket"
                ds = (f"El código bancario {code} de {name} corresponde a {bank}" + (f" ({e['c']})" if e.get("c") else "") + (f", BIC {bics[0]}" if bics else "") + ". Datos del directorio oficial." if es else
                      f"{name} bank code {code} belongs to {bank}" + (f" ({e['c']})" if e.get("c") else "") + (f", BIC {bics[0]}" if bics else "") + ". Data from the official directory.")
                spec = SPECS[pre]
                bp = spec["positions"]["bank"]
                bics_html = " ".join('<span class="pill bic">' + E(b) + "</span>" for b in bics)
                facts = (f'<dl class="facts"><dt>{"Entidad" if es else "Institution"}</dt><dd>{E(bank)}</dd>'
                         + (f'<dt>{"Denominación legal" if es else "Legal name"}</dt><dd>{E(e["ln"])}</dd>' if e.get("ln") else "")
                         + f'<dt>{E(ct)}</dt><dd class="mono">{E(code)}</dd>'
                         + (f'<dt>{"Ciudad" if es else "City"}</dt><dd>{E(e["c"])}</dd>' if e.get("c") else "")
                         + (f'<dt>BIC / SWIFT</dt><dd>{bics_html} '
                            f'<span class="pill {"yes" if e.get("bs") == "CONFIRMED" else "soon"}">{("confirmado" if es else "confirmed") if e.get("bs") == "CONFIRMED" else ("candidato" if es else "candidate")}</span></dd>' if bics else "")
                         + (f'<dt>LEI</dt><dd class="mono">{E(e["l"])}</dd>' if e.get("l") else "")
                         + (f'<dt>{"Estado" if es else "Status"}</dt><dd><span class="pill soon">{"Baja programada" if es else "Deletion scheduled"}</span>'
                            + (f' → <a href="{p_code_item(lang, pre, e["su"])}">{E(e["su"])}</a>' if e.get("su") and e["su"] in d["codes"] else (f" → {E(e['su'])}" if e.get("su") else "")) + "</dd>" if e.get("st") else "")
                         + f'<dt>{"Posición en el IBAN" if es else "Position in the IBAN"}</dt><dd>{"caracteres" if es else "characters"} {bp[0] + 5}–{bp[1] + 4} ({pre}kk…)</dd>'
                         + f'<dt>SEPA Instant</dt><dd>{E({"REGISTERED": "Adherido" if es else "Registered", "FUTURE": "Adhesión futura" if es else "Future participation", "LEFT": "Baja" if es else "Left", "NOT_REGISTERED": "No figura" if es else "Not listed", "UNKNOWN": "Sin BIC verificado" if es else "No verified BIC"}[inst])}'
                         + (f' · <a href="{p_bank(lang, sepa_bic)}">{"ficha SEPA" if es else "SEPA details"}</a>' if hit else "") + "</dd></dl>")
                qas = [((f"¿Qué banco es el código {code} en {name}?" if es else f"Which bank is code {code} in {name}?"),
                        E(f"{bank}" + (f", {e['c']}" if e.get("c") else "") + ".")),
                       (("¿Dónde aparece este código en el IBAN?" if es else "Where does this code appear in the IBAN?"),
                        E((f"En los IBAN de {name} ({spec['length']} caracteres), el código bancario ocupa los caracteres {bp[0] + 5} a {bp[1] + 4}." if es else
                           f"In {name} IBANs ({spec['length']} characters), the bank code occupies characters {bp[0] + 5} to {bp[1] + 4}.")))]
                faq, fs = faq_html(qas, lang)
                body = (f'<div class="hero"><h1>{E(ct)} {E(code)}: {E(bank)}</h1><p class="lead">{E(ds)}</p></div>'
                        + f'<section class="panel">{facts}</section>' + source_note(lang, pre)
                        + f'<h2>{"Identificar otro banco por IBAN" if es else "Identify another bank by IBAN"}</h2>' + tool("identify", lang, "IBAN", f"{pre}00 …") + privacy(lang)
                        + '<div class="prose">' + faq + f'<p><a href="{p_code_country(lang, pre)}">{"Todos los códigos de" if es else "All bank codes in"} {E(name)} →</a></p></div>')
                sch = [fs, {"@context": "https://schema.org", "@type": "BankOrCreditUnion", "name": bank,
                            **({"address": {"@type": "PostalAddress", "addressLocality": e["c"], "addressCountry": SPECS[pre]["iso"]}} if e.get("c") else {}),
                            "identifier": [{"@type": "PropertyValue", "propertyID": ct, "value": code}] + ([{"@type": "PropertyValue", "propertyID": "BIC", "value": bics[0]}] if bics and e.get("bs") == "CONFIRMED" else [])}]
                page(lang, p_code_item(lang, pre, code), ttl, ds, body, {l: p_code_item(l, pre, code) for l in LANGS},
                     crumbs=[(t["nav_code"], p_code(lang)), (name, p_code_country(lang, pre)), (code, p_code_item(lang, pre, code))], schema=sch, nav="code", tool=True)


def regulation(cc, lang):
    group = SPECS.get(cc, {}).get("group")
    iso = SPECS.get(cc, {}).get("iso", cc)
    return SC.regulation_text(iso, country_name_any(cc, lang), lang) if group else ""


def build_iban_pages():
    for lang in LANGS:
        es = lang == "es"
        t = SC.T[lang]
        title = "Validar IBAN gratis en 41 países SEPA | Cryptopocket" if es else "Free IBAN validator for 41 SEPA countries | Cryptopocket"
        desc = ("Valida un IBAN al instante: longitud, estructura, dígitos de control y control nacional. Identifica el banco cuando hay directorio oficial disponible."
                if es else "Validate an IBAN instantly: length, structure, check digits and national check. Identifies the bank where an official directory is available.")
        rows = "".join(f'<tr><td><a href="{p_iban_c(lang, p)}">{E(cname(p, lang))}</a></td><td class="mono">{p}</td><td class="num">{SPECS[p]["length"]}</td><td class="mono">{E(mask(p))}</td></tr>'
                       for p in sorted(SPECS, key=lambda x: cname(x, lang)))
        legend = ("k = dígitos de control · b = código bancario · s = oficina · x = control nacional · c = cuenta" if es else "k = check digits · b = bank code · s = branch · x = national check · c = account")
        qas = [("¿Cómo se valida un IBAN?" if es else "How is an IBAN validated?",
                "Comprobamos el código de país, la longitud y la estructura del país, los dígitos de control ISO 13616 (módulo 97) y, donde existe y está verificado, el control nacional." if es else
                "We check the country code, the country's length and structure, the ISO 13616 check digits (mod 97) and, where one exists and is verified, the national check."),
               ("¿Se guarda el IBAN?" if es else "Is the IBAN stored?", E(t["privacy_note"]))]
        faq, fs = faq_html(qas, lang)
        body = (f'<div class="hero"><h1>{"Validar IBAN" if es else "IBAN validator"}</h1><p class="lead">{E(desc)}</p></div>'
                + tool("iban", lang, "IBAN", "ES00 0000 0000 0000 0000 0000") + privacy(lang)
                + f'<h2>{"Formato del IBAN por país" if es else "IBAN format by country"}</h2><p class="hint">{E(legend)}</p>'
                + f'<div class="tbl"><table><thead><tr><th>{"País" if es else "Country"}</th><th>{"Código" if es else "Code"}</th><th>{"Longitud" if es else "Length"}</th><th>{"Formato" if es else "Format"}</th></tr></thead><tbody>{rows}</tbody></table></div>'
                + '<div class="prose">' + faq + "</div>")
        page(lang, p_iban(lang), title, desc, body, {l: p_iban(l) for l in LANGS}, crumbs=[(t["nav_iban"], p_iban(lang))],
             schema=[web_app("IBAN validator", p_iban(lang), desc), fs], nav="iban", tool=True)

        for p in SPECS:
            s = SPECS[p]
            name = cname(p, lang)
            m = mask(p)
            title = (f"Validar IBAN de {name} e identificar el banco | Cryptopocket" if es else f"{name} IBAN validator and bank lookup | Cryptopocket")
            desc = (f"IBAN de {name}: {s['length']} caracteres, formato {m}. Valida un IBAN {p} y comprueba de qué banco es." if es else
                    f"{name} IBAN: {s['length']} characters, format {m}. Validate a {p} IBAN and find out which bank it belongs to.")
            b = s["positions"].get("bank")
            br = s["positions"].get("branch")
            facts = (f'<dl class="facts"><dt>{"Código de país" if es else "Country code"}</dt><dd class="mono">{p}</dd>'
                     f'<dt>{"Longitud" if es else "Length"}</dt><dd>{s["length"]}</dd><dt>{"Formato" if es else "Format"}</dt><dd class="mono">{E(m)}</dd>'
                     + (f'<dt>{E(code_type(p, lang))}</dt><dd>{"caracteres" if es else "characters"} {b[0] + 5}–{b[1] + 4}</dd>' if b else "")
                     + (f'<dt>{"Oficina" if es else "Branch"}</dt><dd>{"caracteres" if es else "characters"} {br[0] + 5}–{br[1] + 4}</dd>' if br else "")
                     + f'<dt>{"Control nacional" if es else "National check"}</dt><dd>{("Sí" if es else "Yes") if s["national_check"] else ("No aplicado" if es else "Not applied")}</dd>'
                     + f'<dt>{"Identificación del banco" if es else "Bank identification"}</dt><dd>{status_badge(p, lang)}</dd></dl>')
            dirsec = ""
            if p in CATALOG:
                codes = CATALOG[p]["codes"]
                more = (f'<p><a href="{p_code_country(lang, p)}">{"Ver los" if es else "See all"} {fmt_n(len(codes), lang)} {"códigos" if es else "codes"} →</a></p>' if p in CODE_PAGES else "")
                dirsec = (f'<h2>{"Códigos bancarios de" if es else "Bank codes in"} {E(name)}</h2>' + source_note(lang, p) + code_rows(lang, p, codes, limit=100) + more)
            else:
                dirsec = (f'<div class="prose"><p>{E(JS[lang]["dir_pending_p"] if s["directory"] == "pending_licence" else JS[lang]["dir_none_p"])}</p></div>')
            reg = regulation(p, lang)
            sepa_link = (f' <a href="{p_country(lang, s["iso"])}">{"Bancos con SEPA Instant en" if es else "SEPA Instant banks in"} {E(name)} →</a>' if s["iso"] in INST_BYCC else "")
            body = (f'<div class="hero"><h1>{"Validar IBAN de" if es else ""} {E(name)}{"" if es else " IBAN validator"}</h1><p class="lead">{E(desc)}</p></div>'
                    + tool("iban", lang, f"IBAN {p}", m.replace("k", "0").upper()) + privacy(lang)
                    + f'<section class="panel">{facts}</section>' + (f'<div class="prose"><p>{E(reg)}{sepa_link}</p></div>' if reg else "") + dirsec)
            page(lang, p_iban_c(lang, p), title, desc, body, {l: p_iban_c(l, p) for l in LANGS},
                 crumbs=[(t["nav_iban"], p_iban(lang)), (name, p_iban_c(lang, p))], nav="iban", tool=True)


def mask(p):
    s = SPECS[p]
    chars = ["c"] * s["bban_length"]
    for key, ch in (("bank", "b"), ("branch", "s"), ("check", "x")):
        r = s["positions"].get(key)
        if r:
            for i in range(r[0], min(r[1], len(chars))):
                chars[i] = ch
    v = p + "kk" + "".join(chars)
    return " ".join(v[i:i + 4] for i in range(0, len(v), 4))


def build_bic():
    for lang in LANGS:
        es = lang == "es"
        t = SC.T[lang]
        title = "Buscar código BIC / SWIFT y su participación SEPA | Cryptopocket" if es else "BIC / SWIFT code lookup and SEPA participation | Cryptopocket"
        desc = ("Valida un código BIC o SWIFT, descubre a qué entidad y país corresponde, sus códigos nacionales y si está inscrito en SEPA, SEPA Instant y adeudos SEPA."
                if es else "Validate a BIC or SWIFT code, find out which institution and country it belongs to, its national codes and whether it is registered for SEPA, SEPA Instant and SEPA direct debits.")
        struct = [("AAAA", "Entidad: 4 letras" if es else "Institution: 4 letters"), ("BB", "País: código ISO" if es else "Country: ISO code"),
                  ("CC", "Localidad: 2 caracteres" if es else "Location: 2 characters"), ("DDD", "Oficina (opcional); XXX = oficina principal" if es else "Branch (optional); XXX = head office")]
        qas = [("¿BIC y SWIFT son lo mismo?" if es else "Are BIC and SWIFT the same?",
                "Sí. BIC es el nombre oficial del código (ISO 9362); SWIFT es la organización que lo asigna." if es else "Yes. BIC is the official name of the code (ISO 9362); SWIFT is the organisation that issues it."),
               ("¿Qué significa XXX al final?" if es else "What does XXX at the end mean?",
                "La oficina principal. Un BIC de 8 caracteres equivale al mismo código terminado en XXX." if es else "The head office. An 8-character BIC is equivalent to the same code ending in XXX.")]
        faq, fs = faq_html(qas, lang)
        body = (f'<div class="hero"><h1>{"Buscar código BIC / SWIFT" if es else "BIC / SWIFT code lookup"}</h1><p class="lead">{E(desc)}</p></div>'
                + tool("bic", lang, "BIC / SWIFT", "AAAABBCCDDD")
                + f'<h2>{"Estructura de un BIC" if es else "BIC structure"}</h2><div class="tbl"><table><tbody>' + "".join(f'<tr><td class="mono">{a}</td><td>{E(b)}</td></tr>' for a, b in struct) + "</tbody></table></div>"
                + '<div class="prose">' + faq + "</div>")
        page(lang, p_bic(lang), title, desc, body, {l: p_bic(l) for l in LANGS}, crumbs=[(t["nav_bic"], p_bic(lang))],
             schema=[web_app("BIC lookup", p_bic(lang), desc), fs], nav="bic", tool=True)


def inst_table(lang, rows, show_country=False):
    es = lang == "es"
    head = f'<tr><th>{"Entidad" if es else "Institution"}</th><th>BIC</th><th>{"Ciudad" if es else "City"}</th>' + (f'<th>{"País" if es else "Country"}</th>' if show_country else "") + f'<th>SEPA Instant</th></tr>'
    body = []
    for bic, p in rows:
        x = p["s"].get("SCT_INST")
        st = x[2] if x else "NOT_REGISTERED"
        cell = fmt_date(x[0], lang) if st == "REGISTERED" else (f'<span class="pill soon">{"desde" if es else "from"} {fmt_date(x[0], lang)}</span>' if st == "FUTURE" else "–")
        body.append(f'<tr><td><a href="{p_bank(lang, bic)}">{E(p["n"])}</a></td><td class="mono">{bic}</td><td>{E(p["c"])}</td>'
                    + (f'<td>{E(country_name_any(iso_of(bic, p), lang))}</td>' if show_country else "") + f'<td class="num">{cell}</td></tr>')
    return f'<div class="tbl"><table><thead>{head}</thead><tbody>{"".join(body)}</tbody></table></div>'


def build_sepa():
    for lang in LANGS:
        es = lang == "es"
        t = SC.T[lang]
        title = "¿Acepta SEPA Instant? Buscador de bancos | Cryptopocket" if es else "SEPA Instant checker: does the bank accept instant payments? | Cryptopocket"
        desc = (f"Comprueba por BIC, IBAN o nombre si un banco está adherido a SEPA Instant. {fmt_n(N_INST, lang)} entidades en {N_INST_COUNTRIES} países, registro oficial del EPC actualizado a diario."
                if es else f"Check by BIC, IBAN or name whether a bank is registered for SEPA Instant. {fmt_n(N_INST, lang)} institutions in {N_INST_COUNTRIES} countries, official EPC register updated daily.")
        grid = '<div class="grid">' + "".join(f'<a href="{p_country(lang, cc)}">{E(country_name_any(cc, lang))} <span>{len(v)}</span></a>'
                                              for cc, v in sorted(INST_BYCC.items(), key=lambda kv: country_name_any(kv[0], lang))) + "</div>"
        recent = sorted([(b, p) for b, p in SEPA.items() if inst_status(p) == "REGISTERED"], key=lambda bp: bp[1]["s"]["SCT_INST"][0], reverse=True)[:12]
        soon = sorted([(b, p) for b, p in SEPA.items() if inst_status(p) == "FUTURE"], key=lambda bp: bp[1]["s"]["SCT_INST"][0])[:30]
        stats = (f'<div class="stats"><div class="stat"><b>{fmt_n(N_INST, lang)}</b><span>{"Participantes" if es else "Participants"}</span></div>'
                 f'<div class="stat"><b>{N_INST_COUNTRIES}</b><span>{"Países" if es else "Countries"}</span></div>'
                 f'<div class="stat"><b>{E(fmt_date(LATEST, lang))}</b><span>{"Última adhesión" if es else "Latest joiner"}</span></div></div>')
        qas = [("¿Qué es SEPA Instant?" if es else "What is SEPA Instant?",
                (f'El esquema europeo de transferencias inmediatas en euros: máximo 10 segundos, 24/7. <a href="{p_guide(lang, GUIDE["what"])}">Más información</a>.' if es else
                 f'The European scheme for instant euro transfers: within 10 seconds, 24/7. <a href="{p_guide(lang, GUIDE["what"])}">Learn more</a>.')),
               ("¿Y si el banco no aparece?" if es else "What if the bank is not listed?", E(JS[lang]["inst_no_p"]))]
        faq, fs = faq_html(qas, lang)
        body = (f'<div class="hero"><h1>{"¿El banco acepta SEPA Instant?" if es else "Does the bank accept SEPA Instant?"}</h1><p class="lead">{E(desc)}</p></div>'
                + tool("sepa", lang, t["search_ph"], "BIC · IBAN · " + ("nombre del banco" if es else "bank name")) + stats
                + f'<h2>{"Bancos con SEPA Instant por país" if es else "SEPA Instant banks by country"}</h2>' + grid
                + (f'<h2>{"Próximas incorporaciones" if es else "Upcoming joiners"}</h2>' + inst_table(lang, soon, True) if soon else "")
                + f'<h2>{"Adhesiones recientes" if es else "Recent joiners"}</h2>' + inst_table(lang, recent, True) + '<div class="prose">' + faq + "</div>")
        page(lang, p_sepa(lang), title, desc, body, {l: p_sepa(l) for l in LANGS}, crumbs=[(t["nav_sepa"], p_sepa(lang))],
             schema=[web_app("SEPA Instant checker", p_sepa(lang), desc), fs], nav="sepa", tool=True)

        for cc, rows in INST_BYCC.items():
            name = country_name_any(cc, lang)
            n = len(rows)
            title = (f"Bancos con SEPA Instant en {name} ({n}) | Cryptopocket" if es else f"SEPA Instant banks in {name} ({n}) | Cryptopocket")
            desc = (f"Entidades de {name} adheridas a SEPA Instant según el registro oficial del EPC, con BIC y fecha de adhesión." if es else
                    f"Institutions in {name} registered for SEPA Instant according to the official EPC register, with BIC and joining date.")
            reg = regulation(cc, lang) or (SC.regulation_text(cc, name, lang))
            body = (f'<div class="hero"><h1>{"Bancos con SEPA Instant en" if es else "SEPA Instant banks in"} {E(name)}</h1><p class="lead">{E(desc)}</p></div>'
                    + f'<div class="prose"><p>{E(reg)}</p></div>' + tool("sepa", lang, t["search_ph"], "BIC · IBAN") + inst_table(lang, rows))
            page(lang, p_country(lang, cc), title, desc, body, {l: p_country(l, cc) for l in LANGS},
                 crumbs=[(t["nav_sepa"], p_sepa(lang)), (name, p_country(lang, cc))], nav="sepa", tool=True)


def build_banks():
    labels = {"SCT": "SEPA Credit Transfer (SCT)", "SCT_INST": "SEPA Instant (SCT Inst)", "SDD_CORE": "SEPA Direct Debit Core", "SDD_B2B": "SEPA Direct Debit B2B"}
    by8 = {}
    for bic in SEPA:
        by8.setdefault(bic[:8], []).append(bic)
    for bic, p in SEPA.items():
        cc = iso_of(bic, p)
        for lang in LANGS:
            es = lang == "es"
            t = SC.T[lang]
            nm, cn = p["n"], country_name_any(cc, lang)
            st = inst_status(p)
            x = p["s"].get("SCT_INST")
            d = fmt_date(x[0], lang) if x else "–"
            if st == "REGISTERED":
                title = (f"¿{nm} acepta SEPA Instant? Sí · BIC {bic}" if es else f"Does {nm} accept SEPA Instant? Yes · BIC {bic}")
                desc = (f"{nm} ({bic}, {p['c']}, {cn}) está adherido a SEPA Instant desde el {d} según el registro del EPC." if es else f"{nm} ({bic}, {p['c']}, {cn}) has been registered for SEPA Instant since {d} according to the EPC register.")
                verdict = f'<div class="verdict yes"><div class="ic">✓</div><div><h2>{E(JS[lang]["inst_yes"])}</h2><p>{E(JS[lang]["inst_yes_p"])}</p></div></div>'
            elif st == "FUTURE":
                title = (f"¿{nm} acepta SEPA Instant? Desde el {d} · BIC {bic}" if es else f"Does {nm} accept SEPA Instant? From {d} · BIC {bic}")
                desc = (f"{nm} ({bic}, {cn}) se incorpora a SEPA Instant el {d}." if es else f"{nm} ({bic}, {cn}) joins SEPA Instant on {d}.")
                verdict = f'<div class="verdict soon"><div class="ic">…</div><div><h2>{E(JS[lang]["inst_future"])}</h2><p>{E(JS[lang]["inst_future_p"].replace("{d}", d))}</p></div></div>'
            else:
                title = (f"¿{nm} acepta SEPA Instant? No consta · BIC {bic}" if es else f"Does {nm} accept SEPA Instant? Not listed · BIC {bic}")
                desc = (f"{nm} ({bic}, {cn}) figura en los registros SEPA del EPC, pero no en el de SEPA Instant." if es else f"{nm} ({bic}, {cn}) is listed in EPC SEPA registers but not in the SEPA Instant register.")
                verdict = f'<div class="verdict no"><div class="ic">!</div><div><h2>{E(JS[lang]["inst_no"])}</h2><p>{E(JS[lang]["inst_no_p"])}</p></div></div>'
            sch_rows = "".join(
                f'<tr><td>{labels[k]}</td><td>{E({"REGISTERED": JS[lang]["reg"], "FUTURE": JS[lang]["future"], "LEFT": JS[lang]["left"]}[v[2]])}</td><td class="num">{E(fmt_date(v[0], lang))}</td></tr>'
                for k, v in sorted(p["s"].items(), key=lambda kv: list(labels).index(kv[0])))
            schemes = (f'<div class="tbl"><table><thead><tr><th>{"Esquema" if es else "Scheme"}</th><th>{"Estado" if es else "Status"}</th><th>{"Fecha de adhesión" if es else "Readiness date"}</th></tr></thead><tbody>{sch_rows}</tbody></table></div>')
            facts = (f'<dl class="facts"><dt>{"Entidad" if es else "Institution"}</dt><dd>{E(nm)}</dd><dt>BIC / SWIFT</dt><dd><span class="pill bic">{bic}</span></dd>'
                     f'<dt>{"Ciudad" if es else "City"}</dt><dd>{E(p["c"])}</dd><dt>{"País" if es else "Country"}</dt><dd>{E(cn)}</dd></dl>')
            sib = [b for b in by8[bic[:8]] if b != bic][:20]
            sib_html = ("<h2>" + ("Otros BIC de esta entidad" if es else "Other BICs of this institution") + '</h2><ul class="links">'
                        + "".join(f'<li><a href="{p_bank(lang, b)}">{b}</a></li>' for b in sib) + "</ul>") if sib else ""
            qas = [((f"¿{nm} acepta transferencias SEPA Instant?" if es else f"Does {nm} accept SEPA Instant transfers?"),
                    E({"REGISTERED": (f"Figura en el registro SCT Inst del EPC desde el {d}." if es else f"It has been listed in the EPC SCT Inst register since {d}."),
                       "FUTURE": (f"Tiene fecha de incorporación el {d}." if es else f"It is listed with a joining date of {d}.")}.get(st, JS[lang]["inst_no_p"]))),
                   ((f"¿Cuál es el código BIC de {nm}?" if es else f"What is the BIC code of {nm}?"), E(f"{bic}."))]
            faq, fs = faq_html(qas, lang)
            body = (f'<div class="hero"><h1>{"¿" + E(nm) + " acepta SEPA Instant?" if es else "Does " + E(nm) + " accept SEPA Instant?"}</h1><p class="lead">{E(desc)}</p></div>'
                    + verdict + f'<section class="panel">{facts}</section>' + f'<h2>{"Participación en los esquemas SEPA" if es else "SEPA scheme participation"}</h2>' + schemes
                    + f'<div class="prose"><p>{E(regulation(cc, lang) or SC.regulation_text(cc, cn, lang))}</p></div>' + sib_html
                    + f'<h2>{"Identificar otro banco por IBAN" if es else "Identify another bank by IBAN"}</h2>' + tool("identify", lang, "IBAN", "ES00 …") + '<div class="prose">' + faq + "</div>")
            page(lang, p_bank(lang, bic), title, desc, body, {l: p_bank(l, bic) for l in LANGS},
                 crumbs=[(t["nav_sepa"], p_sepa(lang)), (cn, p_country(lang, cc) if cc in INST_BYCC else p_sepa(lang)), (nm, p_bank(lang, bic))],
                 schema=[fs, {"@context": "https://schema.org", "@type": "BankOrCreditUnion", "name": nm,
                              "address": {"@type": "PostalAddress", "addressLocality": p["c"], "addressCountry": cc},
                              "identifier": {"@type": "PropertyValue", "propertyID": "BIC", "value": bic}}], nav="sepa", tool=True)


def build_guides():
    for lang in LANGS:
        es = lang == "es"
        t = SC.T[lang]
        repl = {"{sepa_url}": p_sepa(lang), "{iban_url}": p_iban(lang), "{identify_url}": p_identify(lang), "{vop_url}": p_guide(lang, GUIDE["vop"]),
                "{contact_url}": E(CONTACT_URL), "{participants}": fmt_n(N_INST - N_INST % 100, lang), "{countries}": str(N_INST_COUNTRIES)}
        cards = "".join(f'<a class="card" href="{p_guide(lang, g)}"><h3>{E(g["title"][lang])}</h3><p>{E(g["desc"][lang])}</p></a>' for g in SC.GUIDES)
        desc = ("Guías sobre identificación bancaria, SEPA Instant, el reglamento europeo de pagos inmediatos y la verificación del beneficiario." if es else
                "Guides to bank identification, SEPA Instant, the EU Instant Payments Regulation and Verification of Payee.")
        page(lang, p_guides(lang), f'{t["guides_title"]} | Cryptopocket', desc,
             f'<div class="hero"><h1>{E(t["guides_title"])}</h1><p class="lead">{E(desc)}</p></div><div class="cards">{cards}</div>',
             {l: p_guides(l) for l in LANGS}, crumbs=[(t["nav_guides"], p_guides(lang))], nav="guides")
        for g in SC.GUIDES:
            b = g["body"][lang]
            for k, v in repl.items():
                b = b.replace(k, v)
            others = "".join(f'<li><a href="{p_guide(lang, o)}">{E(o["title"][lang])}</a></li>' for o in SC.GUIDES if o is not g)
            body = (f'<article class="prose"><div class="hero"><h1>{E(g["title"][lang])}</h1><p class="lead">{E(g["desc"][lang])}</p></div>{b}</article>'
                    + f'<h2>{"Prueba la herramienta" if es else "Try the tool"}</h2>' + tool("identify", lang, "IBAN", "ES00 …")
                    + f'<div class="prose"><h2>{"Más guías" if es else "More guides"}</h2><ul>{others}</ul></div>')
            art = {"@context": "https://schema.org", "@type": "Article", "headline": g["title"][lang], "description": g["desc"][lang], "inLanguage": lang,
                   "datePublished": "2026-10-27", "dateModified": UPDATED, "author": {"@type": "Organization", "name": "Cryptopocket"},
                   "publisher": {"@type": "Organization", "name": "Cryptopocket", "url": "https://cryptopocket.io"}, "mainEntityOfPage": PUBLIC_BASE + p_guide(lang, g)}
            page(lang, p_guide(lang, g), f'{g["title"][lang]} | Cryptopocket', g["desc"][lang], body, {l: p_guide(l, g) for l in LANGS},
                 crumbs=[(t["nav_guides"], p_guides(lang)), (g["title"][lang], p_guide(lang, g))], schema=[art], nav="guides", tool=True)


def build_sources():
    for lang in LANGS:
        es = lang == "es"
        rows = []
        for sid, s in sorted(META.get("sources", {}).items()):
            if sid == "epc_register":
                continue
            rows.append(f'<tr><td><a href="{E(s.get("url", ""))}" rel="nofollow noopener">{E(s.get("institution", sid))}</a></td><td class="mono">{E(sid)}</td>'
                        f'<td>{E(s.get("license", ""))}</td><td>{E(s.get("attribution", ""))}</td><td class="num">{E(fmt_date(s.get("effective_date", ""), lang))}</td></tr>')
        title = "Fuentes de datos y licencias | Cryptopocket" if es else "Data sources and licences | Cryptopocket"
        desc = ("Fuentes oficiales y abiertas que usan las herramientas bancarias de Cryptopocket, con sus licencias, atribuciones y fechas." if es else
                "Official and open sources used by Cryptopocket's banking tools, with their licences, attributions and dates.")
        body = (f'<div class="hero"><h1>{"Fuentes de datos y licencias" if es else "Data sources and licences"}</h1><p class="lead">{E(desc)}</p></div>'
                + f'<div class="tbl"><table><thead><tr><th>{"Fuente" if es else "Source"}</th><th>ID</th><th>{"Licencia" if es else "Licence"}</th><th>{"Atribución" if es else "Attribution"}</th><th>{"Datos de" if es else "Data as of"}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
                + '<div class="prose"><p>' + ("Los datos se normalizan (formato, mayúsculas, códigos) y se combinan entre fuentes; no se alteran los hechos publicados. Las fuentes sin licencia de reutilización verificada no se publican. Los registros del EPC se ofrecen como parte de un servicio más amplio y no se explotan comercialmente por sí mismos."
                                              if es else "Data is normalised (format, capitalisation, codes) and combined across sources; published facts are not altered. Sources without verified reuse terms are not published. EPC register data is offered as part of a broader service and is not commercially exploited as such.") + "</p></div>")
        page(lang, p_sources(lang), title, desc, body, {l: p_sources(l) for l in LANGS}, crumbs=[(SC.T[lang]["sources_link"], p_sources(lang))])


SITEMAP_CHUNK = 10000  # límite del protocolo: 50.000 URL / 50 MB por fichero


def write_sitemap():
    """/tools/sitemap.xml es un índice de sitemaps (sitemap-1.xml, sitemap-2.xml…), apto para crecer."""
    names = []
    for i in range(0, len(SITEMAP), SITEMAP_CHUNK):
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
        for path, alts in SITEMAP[i:i + SITEMAP_CHUNK]:
            lines.append(f"<url><loc>{PUBLIC_BASE}{E(path)}</loc><lastmod>{UPDATED}</lastmod>"
                         + "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{PUBLIC_BASE}{E(p)}"/>' for l, p in alts.items()) + "</url>")
        lines.append("</urlset>")
        name = f"sitemap-{i // SITEMAP_CHUNK + 1}.xml"
        names.append(name)
        with open(os.path.join(OUT, "tools", name), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    idx = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    idx += [f"<sitemap><loc>{PUBLIC_BASE}{PREFIX}/{n}</loc><lastmod>{UPDATED}</lastmod></sitemap>" for n in names]
    idx.append("</sitemapindex>")
    with open(os.path.join(OUT, "tools", "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(idx))


def main():
    tools_dir = os.path.join(OUT, "tools")
    if os.path.isdir(tools_dir):
        shutil.rmtree(tools_dir)
    os.makedirs(os.path.join(tools_dir, "assets"))
    shutil.copy(os.path.join(HERE, "site.css"), os.path.join(tools_dir, "assets", "site.css"))
    shutil.copy(os.path.join(HERE, "site.js"), os.path.join(tools_dir, "assets", "site.js"))
    shutil.copy(os.path.join(os.path.dirname(HERE), "web", "engine", "sepa-engine.js"), os.path.join(tools_dir, "assets", "sepa-engine.js"))
    shutil.copytree(DATA, os.path.join(tools_dir, "data", "v2"))
    for fn in (build_hub, build_identify, build_code_pages, build_iban_pages, build_bic, build_sepa, build_banks, build_guides, build_sources):
        fn()
    write_sitemap()
    print(f"OK: {len(SITEMAP)} páginas · {sum(len(fs) for _, _, fs in os.walk(tools_dir))} ficheros en {tools_dir}")


if __name__ == "__main__":
    main()
