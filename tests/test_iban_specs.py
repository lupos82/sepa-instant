"""Especificaciones IBAN de los 41 países SEPA (+ Gibraltar) y reglas de extracción."""
import random
import warnings

import pytest
from schwifty import IBAN

from sepa_tools import countries, ibanspec

warnings.filterwarnings("ignore")
PREFIXES = [c["iban_prefix"] for c in countries.countries()]


def test_41_paises_sepa_mas_gibraltar():
    assert len(countries.sepa_41()) == 41
    assert len(PREFIXES) == 42 and len(set(PREFIXES)) == 42


def test_territorios_usan_prefijo_del_pais():
    t = countries.territory_parent()
    assert t["JE"] == t["GG"] == t["IM"] == "GB"
    assert t["AX"] == "FI" and t["GF"] == "FR" and t["RE"] == "FR"


@pytest.mark.parametrize("prefix", PREFIXES)
def test_extraccion_codigo_bancario_coincide_con_schwifty(prefix):
    spec = ibanspec.spec_for(prefix)
    assert spec["positions"].get("bank"), f"{prefix} sin posición de código bancario"
    rnd = random.Random(prefix)
    for _ in range(20):
        i = IBAN.random(country_code=prefix, random=rnd)
        bban = str(i).replace(" ", "")[4:]
        a, b = spec["positions"]["bank"]
        assert bban[a:b] == i.bank_code
        if spec["positions"].get("branch"):
            a, b = spec["positions"]["branch"]
            assert bban[a:b] == i.branch_code
        assert len(str(i).replace(" ", "")) == spec["length"]


def test_codigos_conservan_ceros_iniciales():
    spec = ibanspec.spec_for("ES")
    bban = "0049" + "0001" + "00" + "0000000000"
    a, b = spec["positions"]["bank"]
    assert bban[a:b] == "0049"


def test_paises_con_codigo_de_prefijo_bic():
    alfa = {p for p in PREFIXES if ibanspec.bank_code_is_bic_prefix(ibanspec.spec_for(p))}
    assert {"GB", "IE", "NL", "BG", "RO", "MT", "GI", "LV"} <= alfa
    assert "ES" not in alfa and "DE" not in alfa
