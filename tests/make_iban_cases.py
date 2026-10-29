"""Genera tests/fixtures/iban_cases.json: IBAN sintéticos con resultado esperado calculado por schwifty.

Los IBAN son aleatorios (semilla fija) y no corresponden a cuentas reales conocidas.
Para cada país: válidos, con dígitos de control IBAN erróneos, con control nacional erróneo
(recalculando los dígitos IBAN para que solo falle el control nacional), longitud errónea y
caracteres inválidos.
"""
import json
import os
import random
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schwifty import IBAN  # noqa: E402
from schwifty.exceptions import SchwiftyException  # noqa: E402

from sepa_tools import countries, ibanspec  # noqa: E402

warnings.filterwarnings("ignore")
OUT = os.path.join(os.path.dirname(__file__), "fixtures", "iban_cases.json")


def iban_checkdigits(cc, bban):
    raw = bban + cc + "00"
    num = "".join(str(int(ch, 36)) for ch in raw)
    return f"{98 - int(num) % 97:02d}"


def schwifty_eval(v):
    try:
        i = IBAN(v, validate_bban=True)
        return {"valid": True, "bank": i.bank_code, "branch": i.branch_code}
    except SchwiftyException as e:
        return {"valid": False, "error": type(e).__name__}


def main():
    rnd = random.Random(20261028)
    cases = []
    for c in countries.countries():
        p = c["iban_prefix"]
        spec = ibanspec.spec_for(p)
        for _ in range(25):
            v = str(IBAN.random(country_code=p, random=rnd)).replace(" ", "")
            ev = schwifty_eval(v)
            cases.append({"iban": v, "country": p, "kind": "valid", "expect_valid": ev["valid"],
                          "bank": ev.get("bank", ""), "branch": ev.get("branch", "")})
            # dígitos IBAN erróneos
            bad = v[:2] + f"{(int(v[2:4]) + 1) % 100:02d}" + v[4:]
            cases.append({"iban": bad, "country": p, "kind": "bad_checksum", "expect_valid": False})
            # control nacional erróneo, IBAN recalculado
            chk = spec["positions"].get("check")
            if chk and spec["national_check"]:
                bban = v[4:]
                a, b = chk
                orig = bban[a:b]
                alt = "".join(("A" if ch == "Z" else chr(ord(ch) + 1)) if ch.isalpha() else str((int(ch) + 1) % 10) for ch in orig)
                bban2 = bban[:a] + alt + bban[b:]
                v2 = p + iban_checkdigits(p, bban2) + bban2
                ev2 = schwifty_eval(v2)
                cases.append({"iban": v2, "country": p, "kind": "bad_national", "expect_valid": ev2["valid"]})
        cases.append({"iban": v[:-1], "country": p, "kind": "incomplete", "expect_valid": False})
        cases.append({"iban": v + "0", "country": p, "kind": "too_long", "expect_valid": False})
        cases.append({"iban": v[:6] + "$" + v[7:], "country": p, "kind": "bad_char", "expect_valid": False})
        cases.append({"iban": " ".join(v[i:i + 4] for i in range(0, len(v), 4)).lower(), "country": p,
                      "kind": "spaced_lower", "expect_valid": schwifty_eval(v)["valid"], "bank": schwifty_eval(v).get("bank", "")})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"specs": ibanspec.all_specs(), "cases": cases}, f, indent=0)
    print(f"{len(cases)} casos en {OUT}")


if __name__ == "__main__":
    main()
