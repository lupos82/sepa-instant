"""Fusión de observaciones en el catálogo bancario publicable.

Reglas (ver DATA_NORMALIZATION.md):
  1. Por país se elige la fuente de directorio con mejor prioridad (número más bajo) que tenga
     datos; las fuentes "fallback_for" solo se usan si su fuente principal no tiene datos.
  2. Solo las fuentes publicables (licencia verificada y publish: true) entran en el catálogo
     público. Las demás cuentan para métricas internas.
  3. Un BIC se publica como CONFIRMED solo si procede de una lista oficial que relaciona código
     y BIC. Por cadena LEI (código oficial -> LEI -> BIC del fichero GLEIF/SWIFT) se publica como
     CANDIDATES. Por convención de prefijo BIC (países con código bancario de 4 letras) también
     como CANDIDATES, y la entidad como IDENTIFIED_BY_BIC_PREFIX.
  4. Si dos fuentes dan BIC distintos para el mismo código, se conservan ambas observaciones,
     se marca el conflicto y prevalece la de mejor prioridad.
  5. Nunca se infiere un banco por similitud de nombres.
"""
from collections import defaultdict

from . import countries, ibanspec, sources
from .util import norm_name, today

SCHEMES = ("SCT", "SCT_INST", "SDD_CORE", "SDD_B2B")


def scheme_status(ready: str, leave: str, on: str) -> str:
    if leave and leave <= on:
        return "LEFT"
    if ready and ready > on:
        return "FUTURE"
    return "REGISTERED"


def build_sepa(snapshots: dict, on: str) -> dict:
    """BIC11 -> participación por esquema (solo fuentes EPC publicables)."""
    out = {}
    for sid, recs in snapshots.items():
        cfg = sources.get(sid)
        if cfg.get("connector") != "epc" or not sources.is_publishable(sid):
            continue
        for r in recs:
            e = out.setdefault(r["bic"], {"n": r["name"], "c": r["city"], "cc": r["country"], "s": {}})
            e["s"][r["scheme"]] = [r["ready"], r["leave"], scheme_status(r["ready"], r["leave"], on)]
            if cfg["scheme"] == "SCT_INST" or not e["n"]:
                e["n"], e["c"] = r["name"], r["city"]
    return dict(sorted(out.items()))


def _lei_maps(snapshots):
    bic2lei, lei2bic = defaultdict(set), defaultdict(set)
    for sid, recs in snapshots.items():
        if sources.get(sid).get("connector") != "gleif_bic_lei" or not sources.is_publishable(sid):
            continue
        for r in recs:
            bic2lei[r["bic"]].add(r["lei"])
            lei2bic[r["lei"]].add(r["bic"])
    return bic2lei, lei2bic


def _lei_names(snapshots):
    names = {}
    for sid, recs in snapshots.items():
        if sources.get(sid).get("connector") == "gleif_lei" and sources.is_publishable(sid):
            for r in recs:
                if r.get("status", "ACTIVE") == "ACTIVE":
                    names[r["lei"]] = r["name"]
    return names


def _pick_bics_for_country(bics, prefix_countries):
    """De un conjunto de BIC, los del país; prefiere oficina principal (XXX)."""
    local = sorted(b for b in bics if b[4:6] in prefix_countries)
    head = [b for b in local if b.endswith("XXX")]
    return head or local


def _directory_sources_by_country(snapshots, publishable_only):
    """país -> lista de (prioridad, sid) de fuentes de directorio con datos."""
    by_cc = defaultdict(list)
    for sid, recs in snapshots.items():
        cfg = sources.get(sid)
        if cfg.get("connector") in ("epc", "gleif_bic_lei", "gleif_lei", "ecb_mfi", None, "none"):
            continue
        if publishable_only and not sources.is_publishable(sid):
            continue
        ccs = {r["country"] for r in recs if r.get("kind") == "bank_code"}
        for cc in ccs:
            by_cc[cc].append((int(cfg.get("priority", 50)), sid))
    chosen = {}
    for cc, lst in by_cc.items():
        lst.sort()
        primary_ids = [s for _, s in lst if not sources.get(s).get("fallback_for")]
        fallbacks = [s for _, s in lst if sources.get(s).get("fallback_for")]
        if primary_ids:
            chosen[cc] = primary_ids[0]
        else:
            chosen[cc] = fallbacks[0]
    return chosen, by_cc


def _aggregate_codes(recs, cc):
    """Agrupa filas por código (un BLZ puede tener varias filas de sucursal)."""
    groups = defaultdict(list)
    for r in recs:
        if r.get("kind") == "bank_code" and r["country"] == cc:
            groups[r["code"]].append(r)
    out = {}
    for code, rows in groups.items():
        rows.sort(key=lambda r: (not r.get("primary"), r.get("name", "")))
        rep = rows[0]
        bics = []
        for r in rows:
            if r.get("bic") and r["bic"] not in bics:
                bics.append(r["bic"])
        if rep.get("bic") and rep["bic"] in bics:
            bics.remove(rep["bic"])
            bics.insert(0, rep["bic"])
        out[code] = {"rep": rep, "bics": bics, "rows": len(rows)}
    return out


def build_directory(snapshots: dict, on: str):
    """Devuelve (catálogo público por prefijo IBAN, conflictos, métricas internas)."""
    specs = ibanspec.all_specs()
    bic2lei, lei2bic = _lei_maps(snapshots)
    lei_names = _lei_names(snapshots)
    pub_choice, _ = _directory_sources_by_country(snapshots, publishable_only=True)
    all_choice, all_by_cc = _directory_sources_by_country(snapshots, publishable_only=False)
    terr = countries.territory_parent()

    catalog, conflicts, internal = {}, [], {}
    for c in countries.countries():
        prefix = c["iban_prefix"]
        spec = specs[prefix]
        # Métricas internas (todas las fuentes, publicables o no)
        if prefix in all_choice:
            sid = all_choice[prefix]
            agg = _aggregate_codes(snapshots[sid], prefix)
            internal[prefix] = {"source": sid, "codes": len(agg), "publishable": sources.is_publishable(sid)}

        entries = {}
        sid = pub_choice.get(prefix)
        if sid:
            agg = _aggregate_codes(snapshots[sid], prefix)
            cfg = sources.get(sid)
            for code, g in sorted(agg.items()):
                rep = g["rep"]
                e = {"n": rep.get("short_name") or rep["name"], "s": sid}
                legal = rep.get("legal_name") or rep["name"]
                if legal and legal != e["n"]:
                    e["ln"] = legal
                if rep.get("city"):
                    e["c"] = rep["city"]
                if rep.get("lei"):
                    e["l"] = rep["lei"]
                if g["bics"]:
                    e["b"], e["bs"], e["br"] = g["bics"], "CONFIRMED", "OFFICIAL_LIST"
                elif rep.get("lei") and lei2bic.get(rep["lei"]):
                    cand = _pick_bics_for_country(lei2bic[rep["lei"]], {prefix} | {k for k, v in terr.items() if v == prefix})
                    if cand:
                        e["b"], e["bs"], e["br"] = cand, "CANDIDATES", "LEI_CHAIN"
                if rep.get("deleted"):
                    e["st"] = "DELETION_SCHEDULED"
                    if rep.get("successor"):
                        e["su"] = rep["successor"]
                if not rep.get("primary", True):
                    e["p"] = 0
                entries[code] = e
            # Conflictos con otras fuentes del mismo país
            for _, other in all_by_cc.get(prefix, []):
                if other == sid:
                    continue
                oagg = _aggregate_codes(snapshots[other], prefix)
                for code, og in oagg.items():
                    if code in entries and og["bics"] and entries[code].get("bs") == "CONFIRMED":
                        if og["bics"][0][:8] != entries[code]["b"][0][:8]:
                            conflicts.append({"country": prefix, "code": code, "chosen": [sid, entries[code]["b"][0]],
                                              "other": [other, og["bics"][0]],
                                              "published_other": sources.is_publishable(other)})
                            entries[code]["x"] = 1
            catalog[prefix] = {"source": sid, "relation": "OFFICIAL_LIST", "codes": entries,
                               "code_type": c["code_type"], "effective_date": "", "attribution": cfg.get("attribution", "")}

        elif ibanspec.bank_code_is_bic_prefix(spec):
            bic_cc = {prefix} | {k for k, v in terr.items() if v == prefix}
            sepa = build_sepa(snapshots, on)
            by_code = defaultdict(dict)
            for bic, p in sepa.items():
                if bic[4:6] in bic_cc:
                    by_code[bic[:4]].setdefault(bic, {"name": p["n"], "city": p["c"], "src": "epc"})
            for bic, leis in bic2lei.items():
                if bic[4:6] in bic_cc and bic.endswith("XXX"):
                    for lei in sorted(leis):
                        if lei in lei_names:
                            by_code[bic[:4]].setdefault(bic, {"name": lei_names[lei], "lei": lei, "src": "gleif"})
            for code, bics in sorted(by_code.items()):
                head = sorted(b for b in bics if b.endswith("XXX")) or sorted(bics)
                names = {norm_name(bics[b]["name"]) for b in head}
                rep = bics[head[0]]
                e = {"n": rep["name"], "b": head, "bs": "CANDIDATES", "br": "BIC_PREFIX_CONVENTION",
                     "s": "epc_register" if rep["src"] == "epc" else "gleif_bic_lei"}
                if rep.get("city"):
                    e["c"] = rep["city"]
                if rep.get("lei"):
                    e["l"] = rep["lei"]
                if len({b[:8] for b in head}) > 1 and len(names) > 1:
                    e["amb"] = 1
                entries[code] = e
            if entries:
                catalog[prefix] = {"source": "epc+gleif", "relation": "BIC_PREFIX_CONVENTION", "codes": entries,
                                   "code_type": c["code_type"], "effective_date": "",
                                   "attribution": "EPC Register of Participants; GLEIF/SWIFT BIC-to-LEI (SWIFT © and database rights); GLEIF LEI (CC0)."}
    return catalog, conflicts, internal


def build_bic_index(catalog: dict, sepa: dict) -> dict:
    """BIC8 -> {n, cc, k: [prefijo:código, ...]} a partir de datos publicables."""
    idx = {}
    for bic, p in sepa.items():
        e = idx.setdefault(bic[:8], {"n": p["n"], "cc": bic[4:6]})
        e.setdefault("sepa", 1)
    for prefix, d in catalog.items():
        for code, e in d["codes"].items():
            for b in e.get("b", [])[:3]:
                if e.get("bs") != "CONFIRMED" and d["relation"] != "BIC_PREFIX_CONVENTION":
                    continue
                x = idx.setdefault(b[:8], {"n": e["n"], "cc": b[4:6]})
                ks = x.setdefault("k", [])
                key = f"{prefix}:{code}"
                if key not in ks and len(ks) < 20:
                    ks.append(key)
    return dict(sorted(idx.items()))


def build_name_index(catalog: dict, sepa: dict) -> list:
    """Lista [clave_normalizada, nombre, país, tipo, referencia] sin duplicados."""
    seen, out = set(), []
    for bic, p in sepa.items():
        key = (norm_name(p["n"]), bic[:8])
        if key in seen:
            continue
        seen.add(key)
        out.append([key[0], p["n"], p["cc"], "bic", bic])
    for prefix, d in catalog.items():
        for code, e in d["codes"].items():
            if e.get("p") == 0:
                continue
            k = (norm_name(e["n"]), f"{prefix}:{code}")
            if k in seen:
                continue
            seen.add(k)
            out.append([k[0], e["n"], prefix, "code", f"{prefix}:{code}"])
    out.sort(key=lambda r: (r[0], r[2], r[4]))
    return out


def contrast_with_ecb(catalog: dict, snapshots: dict) -> dict:
    """Marca con m=1 las entidades cuyo LEI (o RIAD en España) figura en la lista MFI del BCE
    como entidad de crédito o banco central. Es un contraste, no una fuente de nombres."""
    leis, riads = set(), set()
    for sid, recs in snapshots.items():
        if sources.get(sid).get("connector") == "ecb_mfi" and sources.is_publishable(sid):
            for r in recs:
                if r.get("lei"):
                    leis.add(r["lei"])
                riads.add(r["riad"])
    stats = {"ecb_records": len(riads), "matched": 0}
    if not riads:
        return stats
    for prefix, d in catalog.items():
        for code, e in d["codes"].items():
            if (e.get("l") and e["l"] in leis) or (prefix == "ES" and f"ES{code}" in riads):
                e["m"] = 1
                stats["matched"] += 1
    return stats


def build(snapshots: dict, on: str = None) -> dict:
    on = on or today()
    sepa = build_sepa(snapshots, on)
    catalog, conflicts, internal = build_directory(snapshots, on)
    ecb_stats = contrast_with_ecb(catalog, snapshots)
    return {
        "sepa": sepa,
        "catalog": catalog,
        "conflicts": conflicts,
        "internal": internal,
        "ecb_contrast": ecb_stats,
        "bic8": build_bic_index(catalog, sepa),
        "names": build_name_index(catalog, sepa),
    }
