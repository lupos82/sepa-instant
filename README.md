# SEPA Tools 2.0 — Cryptopocket

Motor y herramientas web gratuitas para:

- **Identificar el banco de un IBAN** (código bancario nacional, entidad, BIC cuando está verificado).
- **Validar IBAN** de los 41 países SEPA (+ Gibraltar): longitud, estructura, dígitos ISO 13616 y control nacional verificado.
- **Buscar un banco por código nacional** (código de entidad español, Bankleitzahl, BLZ austriaco, código checo, prefijo BIC…).
- **Buscar BIC/SWIFT** y por **nombre de entidad**.
- **Consultar la participación SEPA** (SCT, SCT Inst, SDD Core, SDD B2B) en los registros del EPC.

Sin APIs comerciales (no usa SwiftRef). Fuentes oficiales y abiertas con licencia verificada, comprobadas cada día con GitHub Actions. Arquitectura estática: el IBAN se procesa en el navegador y no sale de él.

La herramienta original (`index.html`, `participants.json`, `changes.json` en la raíz, publicada en https://sepa.cryptopocket.io) sigue funcionando igual.

## Estructura

| Ruta | Qué es |
|---|---|
| `sepa_tools/` | Motor de datos en Python: conectores, normalización, fusión, controles de calidad, publicación atómica |
| `sepa_tools/connectors/` | Un conector por tipo de fuente (EPC, Bundesbank, OeNB, ČNB, Banco de España, BCE, GLEIF, schwifty) |
| `DATA_SOURCES_REGISTRY.yaml` | Registro maestro de fuentes y licencias (el código lo lee: solo `publish: true` llega a la web) |
| `reference/sepa_countries.json` | Los 41 países SEPA, territorios y prefijos IBAN |
| `data/v2/` | Datos públicos generados (JSON estático): especificaciones IBAN, directorios por país, participación SEPA, índices |
| `state/` | Estado de sincronización, instantáneas por fuente, historial de cambios |
| `web/engine/sepa-engine.js` | Motor JavaScript (navegador y Node) con el contrato de API |
| `site/` | Generador de las páginas SEO ES/EN (`/tools/...`) |
| `tests/` | Pruebas Python, JavaScript y de navegador |
| `docs/` | Documentación (arquitectura, licencias, cobertura, contrato, runbook, seguridad, SEO, informe de pruebas) |
| `integration/` | Paquete para integrar en `web-cryptopocket.io` |

## Uso

```bash
pip install -r requirements.txt            # schwifty==2026.10.1, PyYAML==6.0.3
python -m sepa_tools sync                  # comprueba todas las fuentes, actualiza y publica data/v2
python -m sepa_tools sync --offline        # sin red: instantáneas + paquetes locales
python -m sepa_tools selftest              # controles y "canarios" sobre los datos publicados
python -m sepa_tools check-run             # código 1 si la última ejecución tuvo errores
OUT_DIR=_site python site/build_site.py    # genera la web en _site/tools
```

## Pruebas

```bash
pip install -r requirements-dev.txt
python tests/make_iban_cases.py && python -m pytest -q
python tests/build_fixture_dataset.py && node --test tests/js/engine_iban.test.js tests/js/engine_lookup.test.js
SEPA_TOOLS_ROOT=$PWD/tests/.tmp/root OUT_DIR=$PWD/tests/.tmp/site python site/build_site.py
node tests/e2e/site.e2e.js tests/.tmp/site tests/.tmp/shots     # requiere playwright
```

Resultados de la última ejecución: `docs/TEST_REPORT.md`.

## Automatización

`.github/workflows/main.yml`: pruebas → sincronización diaria (05:17 UTC) → commit solo si los datos cambian → web → GitHub Pages. Si una fuente falla o un canario no cuadra, la ejecución se marca en rojo (correo de GitHub) pero la web se publica con los últimos datos buenos. Ver `docs/DAILY_SYNC_RUNBOOK.md`.

## Documentación

- [ARCHITECTURE](docs/ARCHITECTURE.md) · [DATABASE_SCHEMA](docs/DATABASE_SCHEMA.md) · [DATA_NORMALIZATION](docs/DATA_NORMALIZATION.md)
- [OPEN_DATA_LICENSES](docs/OPEN_DATA_LICENSES.md) · [DATA_SOURCES_REGISTRY.yaml](DATA_SOURCES_REGISTRY.yaml) · [COUNTRY_SOURCES_RESEARCH](docs/COUNTRY_SOURCES_RESEARCH.md)
- [SEPA_41_COUNTRIES_COVERAGE](docs/SEPA_41_COUNTRIES_COVERAGE.md) (generado en cada sincronización)
- [API_CONTRACT](docs/API_CONTRACT.md) · [api_examples.json](docs/api_examples.json)
- [DAILY_SYNC_RUNBOOK](docs/DAILY_SYNC_RUNBOOK.md) · [SECURITY_PRIVACY](docs/SECURITY_PRIVACY.md) · [TEST_REPORT](docs/TEST_REPORT.md)
- [SEO_INTEGRATION](docs/SEO_INTEGRATION.md) · [CHANGELOG](CHANGELOG.md)
- Integración web: [integration/](integration/)

## Atribuciones

Datos: European Payments Council (Register of Participants); Banco de España; Deutsche Bundesbank; Oesterreichische Nationalbank (CC BY 4.0); Česká národní banka; Banco Central Europeo; GLEIF (LEI, CC0) y relación BIC-LEI (SWIFT © and database rights. All rights reserved); estructuras IBAN del SWIFT IBAN Registry vía [schwifty](https://github.com/mdomke/schwifty) (MIT). Detalle en `docs/OPEN_DATA_LICENSES.md`.
