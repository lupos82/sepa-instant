"""Métricas de cobertura reales (calculadas sobre los datos procesados) y matriz de 41 países."""
from . import countries, ibanspec, sources


COMPLETE_VS_OFFICIAL = {"bundesbank_blz", "oenb_sepa_directory", "cnb_bank_codes"}
DERIVED_BUNDLE = {"schwifty_de", "schwifty_at", "schwifty_cz"}


def compute(dataset: dict, state: dict) -> dict:
    specs = ibanspec.all_specs()
    out = {}
    for c in countries.countries():
        p = c["iban_prefix"]
        spec = specs[p]
        d = dataset["catalog"].get(p)
        internal = dataset["internal"].get(p)
        sepa_n = sum(1 for b, x in dataset["sepa"].items() if x["cc"] == c["iso"] or b[4:6] == c["iso"])
        e = {
            "iso": c["iso"], "name": c["es"], "group": c["group"], "structural": True,
            "iban_length": spec["length"], "bank_code_pos": spec["positions"].get("bank"),
            "branch_code_pos": spec["positions"].get("branch"), "national_check": spec["national_check"] or None,
            "sepa_participants_bic": sepa_n,
        }
        if d:
            codes = d["codes"]
            src = d["source"]
            e.update({
                "directory": "published", "source": src, "relation": d["relation"], "codes": len(codes),
                "bic_confirmed": sum(1 for x in codes.values() if x.get("bs") == "CONFIRMED"),
                "bic_candidates": sum(1 for x in codes.values() if x.get("bs") == "CANDIDATES"),
                "without_bic": sum(1 for x in codes.values() if not x.get("b")),
                "ambiguous": sum(1 for x in codes.values() if x.get("amb")),
                "conflicts": sum(1 for x in codes.values() if x.get("x")),
                "deletion_scheduled": sum(1 for x in codes.values() if x.get("st") == "DELETION_SCHEDULED"),
                "confirmed_in_ecb_mfi": sum(1 for x in codes.values() if x.get("m")),
                "effective_date": (state.get(src) or {}).get("effective_date", ""),
                "license": sources.get(src)["license"] if src in sources.all_sources() else "ATTRIBUTION_REQUIRED",
                "coverage": ("complete_vs_official_directory" if src in COMPLETE_VS_OFFICIAL else
                             "derived_bundle" if src in DERIVED_BUNDLE else
                             "partial_credit_institutions_only" if src == "bde_mfi_es" else "not_quantifiable"),
            })
        elif internal:
            e.update({"directory": "pending_licence", "source": internal["source"], "codes_internal": internal["codes"],
                      "license": sources.get(internal["source"])["license"], "coverage": "not_published"})
        else:
            e.update({"directory": "none", "coverage": "no_open_source_verified"})
        out[p] = e
    totals = {
        "countries_structural": len(out),
        "countries_sepa_41": len(countries.sepa_41()),
        "countries_with_published_directory": sum(1 for v in out.values() if v.get("directory") == "published"),
        "countries_pending_licence": sum(1 for v in out.values() if v.get("directory") == "pending_licence"),
        "codes_published": sum(v.get("codes", 0) for v in out.values()),
        "codes_bic_confirmed": sum(v.get("bic_confirmed", 0) for v in out.values()),
        "codes_bic_candidates": sum(v.get("bic_candidates", 0) for v in out.values()),
        "codes_without_bic": sum(v.get("without_bic", 0) for v in out.values()),
        "ambiguous": sum(v.get("ambiguous", 0) for v in out.values()),
        "conflicts": len(dataset["conflicts"]),
        "sepa_bics": len(dataset["sepa"]),
        "bic8_index": len(dataset["bic8"]),
        "names_index": len(dataset["names"]),
        "ecb_mfi_records": dataset.get("ecb_contrast", {}).get("ecb_records", 0),
        "codes_confirmed_in_ecb_mfi": dataset.get("ecb_contrast", {}).get("matched", 0),
    }
    return {"countries": out, "totals": totals}


LABEL = {
    "published": "Publicado", "pending_licence": "Importable, pendiente de licencia", "none": "Sin fuente abierta verificada",
    "complete_vs_official_directory": "Completa respecto al directorio oficial", "partial_credit_institutions_only":
    "Parcial: solo entidades de crédito y banco central", "not_quantifiable": "Cobertura no cuantificable",
    "not_published": "No publicado", "no_open_source_verified": "—",
    "derived_bundle": "Respaldo: copia del directorio oficial incluida en schwifty (solo códigos con BIC); se sustituye por la descarga directa",
}


def markdown(cov: dict, generated: str) -> str:
    t = cov["totals"]
    lines = [
        "# Cobertura SEPA — 41 países",
        "",
        f"Generado automáticamente a partir de los datos procesados ({generated}). No se estima nada: cada cifra sale de `data/v2`.",
        "",
        f"- Países con validación estructural de IBAN: **{t['countries_structural']}** (41 países SEPA + Gibraltar).",
        f"- Países con directorio bancario publicado: **{t['countries_with_published_directory']}**.",
        f"- Países con directorio oficial importable pero sin publicar por licencia no verificada: **{t['countries_pending_licence']}**.",
        f"- Códigos bancarios publicados: **{t['codes_published']}** · BIC confirmado: **{t['codes_bic_confirmed']}** · BIC candidato: **{t['codes_bic_candidates']}** · sin BIC: **{t['codes_without_bic']}**.",
        f"- Ambiguos: **{t['ambiguous']}** · Conflictos entre fuentes: **{t['conflicts']}** · BIC en registros EPC: **{t['sepa_bics']}**.",
        "",
        "| País | IBAN | Código bancario (posiciones BBAN) | Control nacional | Directorio | Fuente | Códigos | BIC confirmados | BIC candidatos | Fecha efectiva | Licencia | Cobertura | BIC en EPC |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for p, v in sorted(cov["countries"].items(), key=lambda kv: kv[1]["name"]):
        pos = v["bank_code_pos"]
        bpos = f"{pos[0] + 1}–{pos[1]}" if pos else "—"
        if v.get("branch_code_pos"):
            b = v["branch_code_pos"]
            bpos += f" (oficina {b[0] + 1}–{b[1]})"
        codes = v.get("codes", v.get("codes_internal", 0))
        codes_txt = f"{codes}" if v["directory"] == "published" else (f"({codes} sin publicar)" if codes else "—")
        lines.append(
            f"| {v['name']} ({p}) | {v['iban_length']} | {bpos} | {v['national_check'] or '—'} | {LABEL[v['directory']]} | "
            f"{v.get('source', '—')} | {codes_txt} | {v.get('bic_confirmed', '—')} | {v.get('bic_candidates', '—')} | "
            f"{v.get('effective_date') or '—'} | {v.get('license', '—')} | {LABEL.get(v['coverage'], v['coverage'])} | {v['sepa_participants_bic']} |")
    lines += [
        "",
        "## Cómo leer la tabla",
        "",
        "- **Directorio publicado**: el código bancario del IBAN se resuelve contra una fuente con licencia verificada.",
        "- **BIC confirmado**: la fuente oficial relaciona código y BIC. **BIC candidato**: relación por LEI (fichero GLEIF/SWIFT) o por convención de prefijo BIC; se muestra como candidato, no como confirmado.",
        "- **Importable, pendiente de licencia**: hay un directorio oficial accesible, pero sus condiciones de reutilización no están verificadas; se activa cambiando `publish: true` en `DATA_SOURCES_REGISTRY.yaml` tras la revisión legal.",
        "- **Cobertura completa respecto al directorio oficial**: se han importado todos los códigos del fichero oficial; no implica que todos los bancos acepten SEPA Instant.",
        "- **Cobertura no cuantificable**: no existe un universo oficial con el que comparar.",
        "- **BIC en EPC**: BIC del país inscritos en al menos un registro de participantes del EPC.",
    ]
    return "\n".join(lines) + "\n"
