"""Especificaciones IBAN de los países SEPA.

Motor: schwifty (MIT), cuyo registro IBAN se genera a partir del IBAN Registry oficial de
SWIFT (ISO 13616). Solo se usan APIs públicas: ``schwifty.IBAN``, ``schwifty.registry
.get_iban_spec`` y ``schwifty.domain.Component``.

Las validaciones nacionales adicionales se replican en el motor JavaScript solo para los
países donde schwifty implementa el algoritmo y se ha verificado la equivalencia con
pruebas cruzadas (tests/test_js_engine.py).
"""
import schwifty
from schwifty import registry
from schwifty.domain import Component

from . import countries

# Algoritmos nacionales replicados en web/engine/sepa-engine.js (mismo código que schwifty).
NATIONAL_CHECKS = {
    "ES": "es_ccc", "BE": "be_mod97", "FR": "fr_rib", "MC": "fr_rib", "IT": "it_cin", "SM": "it_cin",
    "FI": "fi_luhn", "EE": "ee_731", "PL": "pl_weighted", "NO": "no_mod11",
    "PT": "iso7064_97_10", "SI": "iso7064_97_10", "ME": "iso7064_97_10", "MK": "iso7064_97_10",
    "RS": "iso7064_97_10",
}

_COMPONENTS = {
    "bank": Component.BANK_CODE,
    "branch": Component.BRANCH_CODE,
    "account": Component.ACCOUNT_CODE,
    "check": Component.NATIONAL_CHECKSUM_DIGITS,
    "holder": Component.ACCOUNT_HOLDER_ID,
}


def schwifty_version() -> str:
    return getattr(schwifty, "__version__", "unknown")


def spec_for(prefix: str) -> dict:
    sp = registry.get_iban_spec(prefix)
    pos = {}
    for key, comp in _COMPONENTS.items():
        rg = sp.positions.get(comp)
        if rg is not None and rg.end > rg.start:
            pos[key] = [rg.start, rg.end]
    lookup = [c for c in sp.bic_lookup_components]
    return {
        "prefix": prefix,
        "length": sp.iban_length,
        "bban_spec": sp.bban_spec,
        "bban_length": sp.bban_length,
        "bban_regex": sp.regex.pattern,
        "positions": pos,
        "lookup_branch": Component.BRANCH_CODE in lookup,
        "national_check": NATIONAL_CHECKS.get(prefix, ""),
    }


def all_specs() -> dict:
    out = {}
    for c in countries.countries():
        p = c["iban_prefix"]
        out[p] = spec_for(p)
    return out


def bank_code_is_bic_prefix(spec: dict) -> bool:
    """Países cuyo identificador bancario son 4 letras (código de entidad del BIC)."""
    b = spec["positions"].get("bank")
    return bool(b) and b == [0, 4] and spec["bban_spec"].startswith("4!a")
