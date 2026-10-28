"""CLI: python -m sepa_tools <orden>

  sync [--offline] [--only id,id] [--fixtures DIR]   comprobar fuentes, actualizar y publicar data/v2
  check-run                                          sale con código 1 si la última ejecución tuvo errores
  coverage                                           imprime los totales de cobertura
  selftest                                           controles y "canarios" sobre los datos publicados
"""
import argparse
import json
import os
import sys

from . import paths, sync
from .util import read_json


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sepa_tools")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sync")
    s.add_argument("--offline", action="store_true", help="no descarga: usa instantáneas y paquetes locales")
    s.add_argument("--only", default="", help="ids de fuente separados por comas")
    s.add_argument("--fixtures", default="", help="carpeta con ficheros <id_fuente>.<ext> para pruebas")
    s.add_argument("--date", default="", help="fecha de referencia AAAA-MM-DD (pruebas)")
    sub.add_parser("check-run")
    sub.add_parser("coverage")
    sub.add_parser("selftest")
    a = ap.parse_args(argv)

    if a.cmd == "sync":
        fixtures = {}
        if a.fixtures:
            for fn in os.listdir(a.fixtures):
                sid = fn.split(".")[0]
                with open(os.path.join(a.fixtures, fn), "rb") as f:
                    fixtures[sid] = f.read()
        only = {x for x in a.only.split(",") if x} or None
        rep = sync.run(offline=a.offline, only=only, fixtures=fixtures, on=a.date or None)
        print(json.dumps({"data_version": rep["data_version"], "totals": rep["totals"], "errors": rep["errors"],
                          "sources": {k: v.get("status") for k, v in rep["sources"].items()}}, ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "check-run":
        last = read_json(sync.LAST_RUN_FILE, None)
        if not last:
            print("No hay ejecución registrada."); return 1
        errs = last["report"]["errors"]
        for e in errs:
            print(f"::warning::{e}")
        return 1 if errs else 0
    if a.cmd == "selftest":
        from . import selftest
        return 1 if selftest.run() else 0
    if a.cmd == "coverage":
        print(json.dumps(read_json(os.path.join(paths.DATA_DIR, "coverage.json"), {}).get("totals", {}), indent=1))
        return 0


if __name__ == "__main__":
    sys.exit(main())
