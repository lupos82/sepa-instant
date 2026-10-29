"""Construye un conjunto de datos de prueba (fuentes sintéticas + schwifty) en tests/.tmp/root."""
import json
import os
import shutil
import subprocess
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_source_fixtures as mf  # noqa: E402


def build(dest=os.path.join(HERE, ".tmp", "root"), stale=False):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    shutil.copytree(os.path.join(REPO, "reference"), os.path.join(dest, "reference"))
    os.makedirs(os.path.join(dest, "docs"))
    reg = yaml.safe_load(open(os.path.join(REPO, "DATA_SOURCES_REGISTRY.yaml"), encoding="utf-8"))
    for s in reg["sources"]:
        if "min_records" in s:
            s["min_records"] = 1
    # Las pruebas mantienen BE como "pendiente de licencia" para cubrir ese estado
    # (en producción BE se publica por aceptación de riesgo documentada).
    for s in reg["sources"]:
        if s["id"] == "schwifty_be":
            s["publish"] = False
            s.pop("risk_accepted", None)
    with open(os.path.join(dest, "DATA_SOURCES_REGISTRY.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(reg, f, allow_unicode=True, sort_keys=False)
    fx = os.path.join(HERE, ".tmp", "fx")
    mf.write_set(fx, mf.base_set())
    env = dict(os.environ, SEPA_TOOLS_ROOT=dest, PYTHONPATH=REPO)
    subprocess.run([sys.executable, "-m", "sepa_tools", "sync", "--offline", "--fixtures", fx, "--date", "2026-10-28"],
                   env=env, check=True, capture_output=True, cwd=REPO)
    if stale:
        p = os.path.join(dest, "data", "v2", "status.json")
        st = json.load(open(p))
        st["checked"] = "2026-10-01T05:00:00Z"
        st["sources"]["bundesbank_blz"] = {"status": "error", "error": "FetchError: HTTP 503", "last_check": "2026-10-01T05:00:00Z"}
        json.dump(st, open(p, "w"))
    return dest


if __name__ == "__main__":
    print(build(stale="--stale" in sys.argv))
