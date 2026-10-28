"""Controles de calidad antes de aceptar una instantánea o publicar."""


def record_key(r: dict) -> str:
    k = r.get("kind")
    if k == "bank_code":
        return f"{r['country']}:{r['code']}:{r.get('bic','')}:{int(bool(r.get('primary')))}:{r.get('city','')}"
    if k == "sepa":
        return f"{r['scheme']}:{r['bic']}"
    if k == "bic_lei":
        return f"{r['bic']}:{r['lei']}"
    if k == "mfi":
        return r["riad"]
    if k == "lei":
        return r["lei"]
    return repr(sorted(r.items()))


def diff(old: list, new: list) -> dict:
    o = {record_key(r): r for r in old or []}
    n = {record_key(r): r for r in new or []}
    added = [k for k in n if k not in o]
    removed = [k for k in o if k not in n]
    modified = [k for k in n if k in o and n[k] != o[k]]
    return {"added": len(added), "removed": len(removed), "modified": len(modified),
            "added_keys": added[:50], "removed_keys": removed[:50]}


def gate(cfg: dict, old: list, new: list) -> tuple:
    """(aceptado, motivo). Bloquea fuentes vacías, por debajo del mínimo o con bajas masivas."""
    n_new = len(new or [])
    if n_new == 0:
        return False, "sin registros"
    min_records = int(cfg.get("min_records", 1))
    if n_new < min_records:
        return False, f"{n_new} registros (< mínimo {min_records})"
    if old:
        d = diff(old, new)
        ratio = d["removed"] / max(1, len(old))
        limit = float(cfg.get("max_drop_ratio", 0.15))
        if ratio > limit:
            return False, f"desaparecerían {d['removed']} de {len(old)} registros ({ratio:.0%} > {limit:.0%}); requiere revisión"
    return True, ""
