"""Compatibilidad con la herramienta original (sepa.cryptopocket.io).

Genera participants.json, changes.json y status.json con el mismo formato que el antiguo
sync_epc.py (solo SCT Inst, sin participantes que ya salieron del esquema).
"""
from . import countries, paths
from .util import now_utc, read_json, today, write_json_atomic

KEEP_CHANGES = 104


def _iso_to_epc_name():
    m = {}
    for name, iso in countries.load()["epc_country_names"].items():
        m.setdefault(iso, name)
    return m


def write_legacy(sct_inst_records: list, on: str = None) -> dict:
    on = on or today()
    names = _iso_to_epc_name()
    rows = {}
    for r in sct_inst_records:
        if r.get("leave") and r["leave"] <= on:
            continue
        rows[r["bic"]] = {"country": r.get("epc_country") or names.get(r["country"], r["country"]),
                          "name": r["name"], "city": r["city"], "bic": r["bic"], "since": r["ready"]}
    rows = sorted(rows.values(), key=lambda p: (p["country"], p["name"].upper(), p["bic"]))
    prev = read_json(paths.LEGACY_PARTICIPANTS, {"rows": []}) or {"rows": []}
    prev_rows = {p["bic"]: p for p in prev.get("rows", [])}
    new_rows = {p["bic"]: p for p in rows}
    added = [new_rows[b] for b in new_rows if b not in prev_rows]
    removed = [prev_rows[b] for b in prev_rows if b not in new_rows]
    now = now_utc()
    changed = prev.get("rows") != rows
    if changed:
        write_json_atomic(paths.LEGACY_PARTICIPANTS, {"source": "EPC SCT Inst Register of Participants",
                                                      "updated": now, "count": len(rows), "rows": rows})
        if prev_rows and (added or removed):
            ch = read_json(paths.LEGACY_CHANGES, []) or []
            ch.insert(0, {"date": on, "added": added, "removed": removed})
            write_json_atomic(paths.LEGACY_CHANGES, ch[:KEEP_CHANGES])
    write_json_atomic(paths.LEGACY_STATUS, {"checked": now, "count": len(rows)})
    return {"changed": changed, "added": len(added), "removed": len(removed), "count": len(rows)}
