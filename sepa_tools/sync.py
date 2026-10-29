"""Orquestador de la comprobación y actualización diaria.

Para cada fuente con conector:
  comprobar -> descargar si cambió (petición condicional + sha256) -> parsear/validar ->
  control de calidad frente a la instantánea anterior -> aceptar o conservar la anterior.
Después: fusión, métricas, publicación atómica y ficheros de compatibilidad.

Nada de lo que falle borra datos válidos: una fuente caída conserva su última instantánea.
"""
import os

from . import coverage, legacy, merge, paths, publish, quality, sources
from .connectors import make
from .connectors.gleif import GLEIFLeiConnector
from .util import now_utc, read_json, today, write_json_atomic

STATE_FILE = os.path.join(paths.STATE_DIR, "sources_state.json")
HISTORY_FILE = os.path.join(paths.STATE_DIR, "sync_history.json")
CHANGES_FILE = os.path.join(paths.STATE_DIR, "changes_v2.json")
LAST_RUN_FILE = os.path.join(paths.STATE_DIR, "last_run.json")  # no versionado
NETWORK_FREE = {"schwifty_bundle"}
KEEP_HISTORY = 400


def snapshot_path(sid):
    return os.path.join(paths.SNAPSHOT_DIR, f"{sid}.json")


def load_snapshot(sid):
    return read_json(snapshot_path(sid), None)


def save_snapshot(sid, records):
    write_json_atomic(snapshot_path(sid), records)


def _bootstrap_sct_inst_from_legacy():
    """Primera ejecución sin red: convierte participants.json (formato original) en observaciones."""
    from . import countries
    p = read_json(paths.LEGACY_PARTICIPANTS, None)
    if not p or not p.get("rows"):
        return None
    return sorted([{"kind": "sepa", "scheme": "SCT_INST", "bic": r["bic"], "name": r["name"], "address": "",
                    "city": r["city"], "country": countries.epc_name_to_iso(r["country"]) or r["bic"][4:6],
                    "epc_country": r["country"], "ready": r["since"], "leave": "", "options": "",
                    "src": "epc_sct_inst"} for r in p["rows"]], key=lambda r: r["bic"])


def _leis_to_resolve(snapshots):
    from . import ibanspec, countries
    specs = ibanspec.all_specs()
    prefix_cc = set()
    terr = countries.territory_parent()
    for p, s in specs.items():
        if ibanspec.bank_code_is_bic_prefix(s):
            prefix_cc.add(p)
            prefix_cc |= {k for k, v in terr.items() if v == p}
    leis = set()
    for r in snapshots.get("gleif_bic_lei", []) or []:
        if r["bic"][4:6] in prefix_cc and r["bic"].endswith("XXX"):
            leis.add(r["lei"])
    return leis


def run(offline=False, only=None, fixtures=None, on=None) -> dict:
    on = on or today()
    fixtures = fixtures or {}
    reg = sources.all_sources()
    state = read_json(STATE_FILE, {}) or {}
    snapshots, report = {}, {"started": now_utc(), "offline": offline, "sources": {}, "errors": []}

    for sid, cfg in reg.items():
        conn = make(cfg)
        if conn is None or cfg.get("connector") == "gleif_lei":
            continue
        st = state.setdefault(sid, {})
        prev = load_snapshot(sid) if sources.is_publishable(sid) else None
        if prev is None and sid == "epc_sct_inst":
            prev = _bootstrap_sct_inst_from_legacy()
        skip_network = (offline and cfg["connector"] not in NETWORK_FREE and sid not in fixtures) or (only and sid not in only)
        if skip_network:
            if prev is not None:
                snapshots[sid] = prev
            report["sources"][sid] = {"status": "skipped", "records": len(prev or [])}
            continue
        st["last_check"] = now_utc()
        res = conn.run(st, raw_override=fixtures.get(sid))
        entry = {"status": "", "records": 0}
        if not res.ok:
            st["status"], st["error"] = "error", res.error
            entry.update(status="error", error=res.error)
            report["errors"].append(f"{sid}: {res.error}")
            if prev is not None:
                snapshots[sid] = prev
        elif not res.changed:
            st["status"], st["error"] = "unchanged", ""
            st["last_success"] = now_utc()
            entry["status"] = "unchanged"
            if res.version:
                st["version"] = res.version
            if prev is not None:
                snapshots[sid] = prev
            elif res.records:
                snapshots[sid] = res.records
        else:
            ok, why = quality.gate(cfg, prev, res.records)
            if not ok:
                st["status"], st["error"] = "blocked", why
                entry.update(status="blocked", error=why)
                report["errors"].append(f"{sid}: bloqueado por control de calidad: {why}")
                if prev is not None:
                    snapshots[sid] = prev
            else:
                d = quality.diff(prev, res.records)
                snapshots[sid] = res.records
                if sources.is_publishable(sid):
                    save_snapshot(sid, res.records)
                content_changed = d["added"] or d["removed"] or d["modified"] or prev is None
                st.update(status="updated" if content_changed else "unchanged", error="", last_success=now_utc(),
                          sha256=res.sha256, etag=res.etag, last_modified=res.last_modified,
                          records=len(res.records), version=res.version or st.get("version", ""))
                if res.effective_date:
                    st["effective_date"] = res.effective_date
                if content_changed:
                    st["last_change"] = on
                entry.update(status=st["status"], diff={k: d[k] for k in ("added", "removed", "modified")})
        entry["records"] = len(snapshots.get(sid) or [])
        report["sources"][sid] = entry

    # Nombres legales LEI (GLEIF, CC0) para los países con código bancario = prefijo BIC
    lei_sid = "gleif_lei_records"
    prev_lei = load_snapshot(lei_sid) or []
    if offline or (only and lei_sid not in only):
        snapshots[lei_sid] = prev_lei
    else:
        lei_conn = GLEIFLeiConnector(lei_sid)
        r = lei_conn.run_for(_leis_to_resolve(snapshots), prev_lei)
        st = state.setdefault(lei_sid, {})
        st["last_check"] = now_utc()
        if r.ok:
            snapshots[lei_sid] = r.records
            if r.changed:
                save_snapshot(lei_sid, r.records)
                st["last_change"] = on
            st.update(status="updated" if r.changed else "unchanged", error="", last_success=now_utc(),
                      records=len(r.records), effective_date=on if r.changed else st.get("effective_date", ""))
        else:
            snapshots[lei_sid] = prev_lei
            st.update(status="error", error=r.error)
            report["errors"].append(f"{lei_sid}: {r.error}")
        report["sources"][lei_sid] = {"status": st["status"], "records": len(snapshots[lei_sid])}

    # Fusión, métricas y publicación
    dataset = merge.build(snapshots, on)
    cov = coverage.compute(dataset, state)
    changes = read_json(CHANGES_FILE, []) or []
    run_changes = {sid: e["diff"] for sid, e in report["sources"].items()
                   if e.get("diff") and any(e["diff"].values()) and sources.is_publishable(sid)}
    if run_changes:
        changes.insert(0, {"date": on, "sources": run_changes})
        write_json_atomic(CHANGES_FILE, changes[:KEEP_HISTORY])
    pub = publish.publish(dataset, state, cov, changes)
    if "epc_sct_inst" in snapshots:
        report["legacy"] = legacy.write_legacy(snapshots["epc_sct_inst"], on)
    with open(os.path.join(paths.ROOT, "docs", "SEPA_41_COUNTRIES_COVERAGE.md"), "w", encoding="utf-8") as f:
        f.write(coverage.markdown(cov, on))

    # Estado e historial (solo se versiona lo que cambia)
    stable_state = {sid: {k: v for k, v in st.items() if k not in ("last_check", "last_success", "status", "error")}
                    for sid, st in state.items()}
    write_json_atomic(STATE_FILE, stable_state, pretty=True)
    report.update(finished=now_utc(), data_version=pub["data_version"], totals=cov["totals"],
                  conflicts=dataset["conflicts"][:50])
    write_json_atomic(LAST_RUN_FILE, {"report": report, "state": state}, pretty=True)
    if run_changes or report["errors"]:
        hist = read_json(HISTORY_FILE, []) or []
        hist.insert(0, {"date": on, "data_version": pub["data_version"], "errors": report["errors"],
                        "sources": {k: {kk: vv for kk, vv in v.items() if kk != "records"} for k, v in report["sources"].items()
                                    if v.get("status") not in ("skipped", "unchanged")}})
        write_json_atomic(HISTORY_FILE, hist[:KEEP_HISTORY], pretty=True)
    return report
