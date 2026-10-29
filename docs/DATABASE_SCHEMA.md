# Esquema de datos

No hay base de datos relacional: el esquema lógico pedido se materializa en ficheros JSON versionados (estado e instantáneas) y JSON públicos (consulta). Correspondencia:

| Tabla lógica | Dónde vive | Campos |
|---|---|---|
| `countries` | `reference/sepa_countries.json`, `data/v2/iban-specs.json` | `iso`, `name{en,es}`, `group` (eurozone, eu_non_euro, eea, other, territory), `iban_prefix`, `territories[]`, `code_type{en,es}`, `_reference_date` |
| `iban_specs` | `data/v2/iban-specs.json` (por prefijo) | `length`, `bban_spec`, `bban_length`, `bban_regex`, `positions{bank,branch,account,check,holder}` (rango [inicio,fin) en el BBAN), `lookup_branch`, `national_check`, `directory` (published / pending_licence / none), `bic_prefix_rule` · versión = `meta.schwifty` |
| `banks` + `bank_identifiers` | `data/v2/banks/<PREFIJO>.json` → `codes{<código>: entrada}` | `n` nombre, `ln` denominación legal, `c` ciudad, `l` LEI, `st` estado (ausente = ACTIVE, `DELETION_SCHEDULED`), `su` código sucesor, `p:0` si la fila no es principal, `s` fuente, `m:1` contrastado con BCE · fichero: `relation`, `source`, `effective_date`, `attribution`, `code_type` |
| `bic_identifiers` | `codes[].b`, `bs`, `br` y `data/v2/bic8.json` | `b` lista de BIC11, `bs` CONFIRMED / CANDIDATES, `br` OFFICIAL_LIST / LEI_CHAIN / BIC_PREFIX_CONVENTION, `amb:1` ambiguo, `x:1` conflicto · `bic8.json`: `{BIC8: {n, cc, k:["PRE:código"], sepa}}` |
| `sepa_participation` | `data/v2/sepa.json` | `{BIC11: {n, c, cc, s: {SCT|SCT_INST|SDD_CORE|SDD_B2B: [readiness, leaving, REGISTERED|FUTURE|LEFT]}}}` · versión EPC = `meta.sources.epc_*.effective_date` |
| `data_sources` | `DATA_SOURCES_REGISTRY.yaml`, `data/v2/meta.json.sources` | id, institución, países, URL, licencia, términos, condiciones, atribución, prioridad, `publish`, fecha efectiva, registros, último cambio |
| `sync_history` | `state/sync_history.json` (solo ejecuciones con cambios o errores), `state/last_run.json` (última, no versionado), logs de Actions | fecha, versión de datos, errores, por fuente: estado y diff (altas, bajas, modificaciones) |
| `coverage_metrics` | `data/v2/coverage.json`, `docs/SEPA_41_COUNTRIES_COVERAGE.md` | por país: soporte estructural, posiciones, directorio, fuente, códigos, BIC confirmados/candidatos, sin BIC, ambiguos, conflictos, bajas programadas, fecha, licencia, cobertura; totales |

Otros ficheros:

| Fichero | Contenido |
|---|---|
| `state/sources_state.json` | Por fuente: sha256, ETag, Last-Modified, fecha efectiva, nº registros, versión, último cambio (sin marcas horarias volátiles) |
| `state/snapshots/<fuente>.json` | Observaciones normalizadas de cada fuente publicable (permiten restaurar y calcular diferencias) |
| `state/changes_v2.json` / `data/v2/changes.json` | Historial de cambios por fecha y fuente |
| `data/v2/names.json` | `[clave_normalizada, nombre, país, "bic"|"code", referencia]` |
| `data/v2/status.json` | Volátil (no versionado): hora de comprobación y estado por fuente |

Las observaciones normalizadas (`state/snapshots`) tienen `kind`: `bank_code` (country, code, primary, name, short_name, legal_name, city, bic, lei, deleted, successor, relation, src), `sepa` (scheme, bic, name, address, city, country, epc_country, ready, leave, options, src), `bic_lei` (bic, lei), `lei` (lei, name, country, status, checked), `mfi` (riad, lei, country, name, category, city, head_riad, head_lei).
