"""Publicación atómica del conjunto de datos público (data/v2).

Los ficheros versionados son deterministas: si los datos no cambian, el contenido es idéntico
y no se genera commit. La información volátil (hora de la última comprobación) va en
data/v2/status.json, que no se versiona (se despliega en cada ejecución).
"""
import os
import shutil

from . import DATA_SCHEMA_VERSION, __version__, countries, ibanspec, paths, sources
from .util import dumps, now_utc, read_json, sha256_bytes, write_json_atomic

PUBLIC_ATTRIBUTION_IDS = ("epc_sct_inst", "bde_mfi_es", "bundesbank_blz", "oenb_sepa_directory", "cnb_bank_codes",
                          "ecb_mfi", "gleif_bic_lei", "gleif_lei_records", "swift_iban_registry")


def _write(dirpath, name, obj):
    path = os.path.join(dirpath, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(dumps(obj))


MAX_PUBLISHED_DROP = 0.15


def _validate(tmp: str, dataset: dict):
    """Comprobaciones antes de sustituir la versión publicada. Si algo falla, no se publica."""
    specs = read_json(os.path.join(tmp, "iban-specs.json"))
    if not specs or len(specs) < 41:
        raise ValueError("iban-specs.json incompleto")
    sepa = read_json(os.path.join(tmp, "sepa.json"))
    if sepa is None:
        raise ValueError("sepa.json no generado")
    prev_sepa = read_json(os.path.join(paths.DATA_DIR, "sepa.json"), None)
    if prev_sepa and len(sepa) < (1 - MAX_PUBLISHED_DROP) * len(prev_sepa):
        raise ValueError(f"sepa.json pasaría de {len(prev_sepa)} a {len(sepa)} BIC")
    for prefix in dataset["catalog"]:
        d = read_json(os.path.join(tmp, "banks", f"{prefix}.json"))
        if not d or not d.get("codes"):
            raise ValueError(f"banks/{prefix}.json sin códigos")
    prev_dir = os.path.join(paths.DATA_DIR, "banks")
    if os.path.isdir(prev_dir):
        for f in os.listdir(prev_dir):
            prev = read_json(os.path.join(prev_dir, f), {}) or {}
            new = read_json(os.path.join(tmp, "banks", f), None)
            n_prev = len(prev.get("codes", {}))
            n_new = len((new or {}).get("codes", {}))
            if n_prev and n_new < (1 - MAX_PUBLISHED_DROP) * n_prev:
                raise ValueError(f"banks/{f}: pasaría de {n_prev} a {n_new} códigos; requiere revisión")


def publish(dataset: dict, state: dict, coverage: dict, changes_log: list) -> dict:
    specs = ibanspec.all_specs()
    cmap = countries.by_iso()
    tmp = paths.DATA_DIR + ".tmp"
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)

    # Especificaciones + datos del país (nombre, grupo, tipo de código, directorio)
    spec_out = {}
    for c in countries.countries():
        p = c["iban_prefix"]
        s = dict(specs[p])
        s.update({"iso": c["iso"], "name": {"en": c["en"], "es": c["es"]}, "group": c["group"],
                  "code_type": c["code_type"], "territories": c.get("territories", []),
                  "directory": "published" if p in dataset["catalog"] else
                  ("pending_licence" if dataset["internal"].get(p) else "none"),
                  "bic_prefix_rule": ibanspec.bank_code_is_bic_prefix(s)})
        spec_out[p] = s
    _write(tmp, "iban-specs.json", spec_out)

    for prefix, d in dataset["catalog"].items():
        src = d["source"]
        st = state.get(src, {}) if src in state else {}
        _write(tmp, f"banks/{prefix}.json", {
            "country": prefix, "relation": d["relation"], "source": src,
            "effective_date": st.get("effective_date", ""), "attribution": d.get("attribution", ""),
            "code_type": d["code_type"], "codes": d["codes"]})
    _write(tmp, "sepa.json", dataset["sepa"])
    _write(tmp, "bic8.json", dataset["bic8"])
    _write(tmp, "names.json", dataset["names"])
    _write(tmp, "coverage.json", coverage)
    _write(tmp, "changes.json", changes_log[:120])

    src_meta = {}
    for sid, cfg in sources.all_sources().items():
        if not cfg.get("publish"):
            continue
        st = state.get(sid, {})
        src_meta[sid] = {"institution": cfg["institution"], "license": cfg["license"], "url": cfg.get("info_url") or cfg["url"],
                         "terms_url": cfg.get("terms_url", ""), "attribution": cfg.get("attribution", ""),
                         "effective_date": st.get("effective_date", ""), "records": st.get("records", 0),
                         "last_change": st.get("last_change", "")}
    src_meta["epc_register"] = dict(src_meta.get("epc_sct_inst", {}), institution="European Payments Council (EPC)")
    body = {k: read_json(os.path.join(tmp, k)) for k in ("iban-specs.json", "sepa.json", "bic8.json", "names.json")}
    data_version = sha256_bytes(dumps([body, dataset["catalog"]]).encode())[:16]
    schemes = sorted({k for e in dataset["sepa"].values() for k in e["s"]})
    _write(tmp, "meta.json", {"schema": DATA_SCHEMA_VERSION, "engine": __version__, "schemes_available": schemes,
                              "schwifty": ibanspec.schwifty_version(), "data_version": data_version,
                              "sources": src_meta, "conflicts": len(dataset["conflicts"])})
    _validate(tmp, dataset)

    old = paths.DATA_DIR + ".prev"
    if os.path.isdir(old):
        shutil.rmtree(old)
    if os.path.isdir(paths.DATA_DIR):
        os.replace(paths.DATA_DIR, old)
    os.replace(tmp, paths.DATA_DIR)
    if os.path.isdir(old):
        shutil.rmtree(old)
    write_json_atomic(os.path.join(paths.DATA_DIR, "status.json"),
                      {"checked": now_utc(), "data_version": data_version,
                       "sources": {k: {"status": v.get("status", ""), "last_check": v.get("last_check", ""),
                                       "last_success": v.get("last_success", ""), "error": v.get("error", "")}
                                   for k, v in state.items() if k in src_meta}})
    return {"data_version": data_version}
