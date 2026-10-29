"""Pruebas de conectores, fusión y sincronización con ficheros sintéticos en formato real.

Cada prueba trabaja en una raíz temporal aislada (SEPA_TOOLS_ROOT) y ejecuta el CLI real.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_source_fixtures as mf  # noqa: E402

DATE = "2026-10-28"


def make_root(tmp_path, scale_min=True):
    root = tmp_path / "root"
    shutil.copytree(os.path.join(REPO, "reference"), root / "reference")
    (root / "docs").mkdir()
    reg = yaml.safe_load(open(os.path.join(REPO, "DATA_SOURCES_REGISTRY.yaml"), encoding="utf-8"))
    if scale_min:
        for s in reg["sources"]:
            if "min_records" in s:
                s["min_records"] = 1
    with open(root / "DATA_SOURCES_REGISTRY.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(reg, f, allow_unicode=True, sort_keys=False)
    return root


def run_sync(root, fixtures_dir, extra=()):
    env = dict(os.environ, SEPA_TOOLS_ROOT=str(root), PYTHONPATH=REPO)
    cmd = [sys.executable, "-m", "sepa_tools", "sync", "--offline", "--date", DATE]
    if fixtures_dir:
        cmd += ["--fixtures", str(fixtures_dir)]
    p = subprocess.run(cmd + list(extra), env=env, capture_output=True, text=True, cwd=REPO)
    assert p.returncode == 0, p.stderr[-3000:]
    return json.loads(p.stdout)


def jl(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def base(tmp_path):
    root = make_root(tmp_path)
    fx = tmp_path / "fx"
    mf.write_set(fx, mf.base_set())
    out = run_sync(root, fx)
    return root, fx, out


# ----------------------------------------------------------------------- conectores y fusión

def test_descarga_inicial_publica_paises(base):
    root, _, out = base
    assert not out["errors"], out["errors"]
    specs = jl(root, "data/v2/iban-specs.json")
    assert len(specs) == 42
    assert specs["ES"]["directory"] == "published"
    assert specs["FR"]["directory"] == "none"           # FIB de pago: sin directorio
    assert specs["BE"]["directory"] == "pending_licence"  # NBB: licencia no verificada


def test_es_codigo_con_ceros_y_bic_por_cadena_lei(base):
    root, _, _ = base
    es = jl(root, "data/v2/banks/ES.json")
    assert es["source"] == "bde_mfi_es"
    e = es["codes"]["9901"]
    assert e["n"] == "ENTIDAD DE PRUEBA UNO, S.A."
    assert e["b"] == ["TSTAESM1XXX"] and e["bs"] == "CANDIDATES" and e["br"] == "LEI_CHAIN"
    # sin LEI -> sin BIC (no se inventa)
    assert "b" not in es["codes"]["9903"]
    # fondos monetarios excluidos; banco central incluido
    assert "9000" in es["codes"] and len([k for k in es["codes"] if not k.isdigit()]) == 0
    # BIC de sucursal (TSTBESB1BIL) descartado en favor de la oficina principal XXX
    assert es["codes"]["9902"]["b"] == ["TSTBESB1XXX"]


def test_de_bundesbank_directo_prioriza_sobre_schwifty(base):
    root, _, _ = base
    de = jl(root, "data/v2/banks/DE.json")
    assert de["source"] == "bundesbank_blz"
    assert de["codes"]["10010099"]["b"] == ["TSTCDEB1XXX"] and de["codes"]["10010099"]["bs"] == "CONFIRMED"
    assert de["codes"]["10010099"]["c"] == "Berlin"     # fila principal (Merkmal 1)
    z = de["codes"]["20020099"]
    assert z["st"] == "DELETION_SCHEDULED" and z["su"] == "10010099"
    assert "b" not in de["codes"]["30030099"]


def test_at_cz_oficiales(base):
    root, _, _ = base
    at = jl(root, "data/v2/banks/AT.json")
    assert at["source"] == "oenb_sepa_directory"
    assert at["codes"]["99901"]["b"] == ["TSTDATW1XXX"] and at["codes"]["99901"]["c"] == "Wien"
    cz = jl(root, "data/v2/banks/CZ.json")
    assert cz["codes"]["9901"]["b"] == ["TSTKCZPPXXX"]
    assert "b" not in cz["codes"]["9902"]


def test_prefijo_bic_y_ambiguedad(base):
    root, _, _ = base
    gb = jl(root, "data/v2/banks/GB.json")
    e = gb["codes"]["TSTF"]
    assert e["br"] == "BIC_PREFIX_CONVENTION" and e["bs"] == "CANDIDATES"
    assert e.get("amb") == 1                      # dos entidades distintas con el mismo prefijo
    nl = jl(root, "data/v2/banks/NL.json")
    assert nl["codes"]["TSTE"]["n"] == "Proefbank N.V." and "amb" not in nl["codes"]["TSTE"]


def test_sepa_estados_y_duplicados(base):
    root, _, _ = base
    s = jl(root, "data/v2/sepa.json")
    assert s["TSTGFRPPXXX"]["s"]["SCT_INST"][2] == "FUTURE"
    assert s["TSTHFRPPXXX"]["s"]["SCT_INST"][2] == "LEFT"
    assert s["TSTAESM1XXX"]["s"]["SCT_INST"][2] == "REGISTERED"
    assert set(s["TSTAESM1XXX"]["s"]) == {"SCT", "SCT_INST", "SDD_CORE", "SDD_B2B"}


def test_ficheros_compatibles_con_herramienta_original(base):
    root, _, _ = base
    p = jl(root, "participants.json")
    assert set(p) == {"source", "updated", "count", "rows"}
    row = p["rows"][0]
    assert set(row) == {"country", "name", "city", "bic", "since"}
    bics = {r["bic"] for r in p["rows"]}
    assert "TSTHFRPPXXX" not in bics       # salió del esquema: no aparece (comportamiento original)
    assert "TSTGFRPPXXX" in bics           # fecha futura: aparece con fecha (el frontal la marca)
    assert len([r for r in p["rows"] if r["bic"] == "TSTAESM1XXX"]) == 1


def test_trazabilidad_y_atribucion(base):
    root, _, _ = base
    meta = jl(root, "data/v2/meta.json")
    for sid in ("bde_mfi_es", "bundesbank_blz", "epc_sct_inst", "gleif_bic_lei"):
        assert meta["sources"][sid]["attribution"]
        assert meta["sources"][sid]["license"] in ("ATTRIBUTION_REQUIRED", "VERIFIED_PUBLIC_USE")
    # ninguna fuente no publicable aparece en los datos públicos
    for f in os.listdir(os.path.join(root, "data/v2/banks")):
        d = jl(root, f"data/v2/banks/{f}")
        assert not d["source"].startswith("schwifty_be")
        for e in d["codes"].values():
            assert e["s"] in meta["sources"], e


# ----------------------------------------------------------------------- sincronización

def _published_bytes(root):
    out = {}
    base = os.path.join(root, "data", "v2")
    for dp, _, fs in os.walk(base):
        for f in fs:
            if f == "status.json":
                continue
            p = os.path.join(dp, f)
            out[os.path.relpath(p, base)] = open(p, "rb").read()
    return out


def test_actualizacion_sin_cambios_es_idempotente(base):
    root, fx, _ = base
    before = _published_bytes(root)
    hist_before = jl(root, "state/sync_history.json")
    run_sync(root, fx)
    assert _published_bytes(root) == before
    assert jl(root, "state/sync_history.json") == hist_before   # sin cambios: no se añade historial


def test_nuevos_registros_y_modificaciones(base, tmp_path):
    root, _, _ = base
    files = mf.base_set()
    files["bde_mfi_es"] = mf.bde_csv([
        ["ES9901", mf.LEI_A, "ENTIDAD DE PRUEBA UNO RENOMBRADA, S.A.", "Entidad de crédito", "", "Sí", "", "9901"],
        ["ES9902", mf.LEI_B, "ENTIDAD DE PRUEBA DOS, S.A.", "Entidad de crédito", "", "Sí", "", "9902"],
        ["ES9903", "", "ENTIDAD DE PRUEBA TRES, S.A.", "Entidad de crédito", "", "No", "", "9903"],
        ["ES9904", "", "ENTIDAD DE PRUEBA CUATRO, S.A.", "Entidad de crédito", "", "Sí", "", "9904"],
        ["ES9000", "", "BANCO DE ESPAÑA", "Banco central", "", "Sí", "", "9000"]])
    fx2 = tmp_path / "fx2"
    mf.write_set(fx2, files)
    out = run_sync(root, fx2)
    assert out["sources"]["bde_mfi_es"] == "updated"
    es = jl(root, "data/v2/banks/ES.json")
    assert "9904" in es["codes"] and es["codes"]["9901"]["n"].endswith("RENOMBRADA, S.A.")
    ch = jl(root, "state/changes_v2.json")
    assert ch[0]["sources"]["bde_mfi_es"]["added"] >= 1


def test_bajas_masivas_bloqueadas(base, tmp_path):
    root, _, _ = base
    files = mf.base_set()
    files["bde_mfi_es"] = mf.bde_csv([["ES9901", mf.LEI_A, "ENTIDAD DE PRUEBA UNO, S.A.", "Entidad de crédito", "", "Sí", "", "9901"]])
    fx2 = tmp_path / "fx2"
    mf.write_set(fx2, files)
    out = run_sync(root, fx2)
    assert out["sources"]["bde_mfi_es"] == "blocked"
    assert any("bde_mfi_es" in e and "revisión" in e for e in out["errors"])
    assert len(jl(root, "data/v2/banks/ES.json")["codes"]) == 4   # se conserva la versión anterior


def test_fichero_corrupto_conserva_version_anterior(base, tmp_path):
    root, _, _ = base
    files = mf.base_set()
    files["bundesbank_blz"] = b"\x00\x01 basura <html>Service unavailable</html>"
    files["epc_sct_inst"] = b"<html>Maintenance</html>"
    fx2 = tmp_path / "fx2"
    mf.write_set(fx2, files)
    out = run_sync(root, fx2)
    assert out["sources"]["bundesbank_blz"] == "error"
    assert out["sources"]["epc_sct_inst"] == "error"
    assert "10010099" in jl(root, "data/v2/banks/DE.json")["codes"]
    assert "TSTAESM1XXX" in jl(root, "data/v2/sepa.json")


def test_fuente_caida_y_fallback(tmp_path):
    root = make_root(tmp_path)
    files = mf.base_set()
    del files["bundesbank_blz"]                    # sin descarga directa: se usa la copia de schwifty
    fx = tmp_path / "fx"
    mf.write_set(fx, files)
    run_sync(root, fx)
    de = jl(root, "data/v2/banks/DE.json")
    assert de["source"] == "schwifty_de" and len(de["codes"]) > 3000


def test_conflicto_entre_fuentes_marcado(tmp_path):
    root = make_root(tmp_path)
    files = mf.base_set()
    files["bundesbank_blz"] = mf.bundesbank_txt([
        ["10000000", "1", "Prüf-Notenbank", "10117", "Berlin", "Prüf-Notenbank", "", "TSTZDEFFXXX", "09", "000001", "U", "0", "00000000"]])
    fx = tmp_path / "fx"
    mf.write_set(fx, files)
    run_sync(root, fx)
    de = jl(root, "data/v2/banks/DE.json")
    assert de["codes"]["10000000"]["b"] == ["TSTZDEFFXXX"]   # gana la fuente de mejor prioridad
    assert de["codes"]["10000000"].get("x") == 1             # y se marca el conflicto con schwifty_de
    assert jl(root, "data/v2/meta.json")["conflicts"] >= 1


def test_publicacion_atomica_no_deja_restos(base):
    root, _, _ = base
    assert not os.path.exists(os.path.join(root, "data", "v2.tmp"))
    assert not os.path.exists(os.path.join(root, "data", "v2.prev"))


def test_publicacion_fallida_no_toca_datos(base):
    root, _, _ = base
    before = _published_bytes(root)
    code = f"""
import sys; sys.path.insert(0, {REPO!r})
import os; os.environ['SEPA_TOOLS_ROOT']={str(root)!r}
from sepa_tools import publish
try:
    publish.publish({{'catalog': {{'XX': {{'source': 'x', 'relation': 'OFFICIAL_LIST', 'codes': {{}}, 'code_type': {{}}}}}},
                     'internal': {{}}, 'sepa': {{}}, 'bic8': {{}}, 'names': [], 'conflicts': []}}, {{}}, {{}}, [])
except Exception as e:
    print('FALLO', e)
"""
    p = subprocess.run([sys.executable, "-c", code], env=dict(os.environ, SEPA_TOOLS_ROOT=str(root)), capture_output=True, text=True)
    assert "FALLO" in p.stdout, p.stdout + p.stderr
    assert _published_bytes(root) == before


def test_registro_rechaza_publicar_fuentes_sin_licencia(tmp_path):
    root = make_root(tmp_path)
    reg = yaml.safe_load(open(root / "DATA_SOURCES_REGISTRY.yaml", encoding="utf-8"))
    for s in reg["sources"]:
        if s["id"] == "schwifty_be":
            s["publish"] = True
    with open(root / "DATA_SOURCES_REGISTRY.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(reg, f, allow_unicode=True)
    env = dict(os.environ, SEPA_TOOLS_ROOT=str(root), PYTHONPATH=REPO)
    p = subprocess.run([sys.executable, "-m", "sepa_tools", "sync", "--offline"], env=env, capture_output=True, text=True, cwd=REPO)
    assert p.returncode != 0 and "publish=true no permitido" in p.stderr


def test_contraste_con_lista_mfi_del_bce(base):
    root, _, _ = base
    es = jl(root, "data/v2/banks/ES.json")
    assert es["codes"]["9901"].get("m") == 1      # LEI y RIAD presentes en la lista MFI de prueba
    assert "m" not in es["codes"]["9903"]
    cov = jl(root, "data/v2/coverage.json")
    assert cov["totals"]["codes_confirmed_in_ecb_mfi"] >= 1


def test_bde_cabecera_real_2026_y_categorias_variables():
    """Cabecera observada en la descarga real del 29-10-2026 (codigoDeSupervisor) y categorías con otra redacción."""
    from sepa_tools.connectors.national import BdEMFIConnector
    con = BdEMFIConnector("bde_mfi_es")
    hdr = "codigoEuropeo;lei;nombre;categoria;direccion;informe;entidadMatriz;codigoDeSupervisor\n"
    raw = (hdr + "ES9901;;ENTIDAD UNO, S.A.;ENTIDADES DE CREDITO;Madrid;S;;9901\n"
           "ESX1;;FONDO DE PRUEBA;FONDOS DEL MERCADO MONETARIO;;S;;\n").encode("utf-8")
    recs = con.parse(raw, None)
    assert [r["code"] for r in recs] == ["9901"]
    # categoría en otro formato (código sectorial): se aceptan las filas con código de supervisor de 4 dígitos
    raw2 = (hdr + "ES0049;;BANCO DE PRUEBA, S.A.;XYZ;Santander;S;;0049\nESX2;;FONDO;MMF;;S;;\n").encode("utf-8")
    assert [r["code"] for r in con.parse(raw2, None)] == ["0049"]
