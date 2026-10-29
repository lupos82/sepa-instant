# Contrato de la API (motor `sepa-engine.js` 2.0.0)

No hay API de servidor: el contrato es el del motor JavaScript, que se ejecuta en el navegador (o en Node) sobre los JSON estáticos de `data/v2`. Así el IBAN nunca se envía a ningún servidor. Ejemplos reales de respuesta (generados por las pruebas con datos de prueba): [`api_examples.json`](api_examples.json).

## Uso

```html
<script src="/tools/assets/sepa-engine.js"></script>
<script>
  const engine = SepaEngine.create({ baseUrl: '/tools/data/v2/' });
  engine.identifyByIban('ES91 2100 0418 4502 0005 1332').then(r => console.log(r.bank_identification_status, r.bank_name));
</script>
```

```js
// Node ≥ 18
const SepaEngine = require('./web/engine/sepa-engine.js');
const engine = SepaEngine.create({ baseUrl: 'https://cryptopocket.io/tools/data/v2/' });
```

`create(opts)`: `baseUrl` (por defecto `/data/v2/`), `fetchJSON(url)` (inyectable; por defecto `fetch` sin credenciales), `now()` (inyectable para pruebas). Cada fichero se descarga una vez por instancia.

## Funciones

| Función | Devuelve |
|---|---|
| `normalizeIban(texto)` | IBAN en mayúsculas sin espacios, guiones, puntos ni prefijo "IBAN" (síncrona) |
| `normalizeBic(texto)` | BIC de 11 caracteres o `''` si el formato no es válido (síncrona) |
| `validateIban(iban)` | `{input_normalized, country_code, country_name, iban_structure_valid, iban_checksum_valid, national_check, iban_valid, formatted, expected_length?, errors[]}` |
| `extractBankCode(iban)` | `{country_code, national_bank_code, branch_code, national_bank_code_type, lookup_key}` o `null` |
| `identifyByIban(iban)` | Resultado de identificación (abajo) |
| `identifyByCode(país, código)` | Resultado de identificación; acepta código con o sin oficina cuando el país la usa |
| `lookupBic(bic)` | `{bic, bic_valid, institution_code, country_code, location_code, branch_code, is_head_office, is_test_bic, country_name, bank_name, national_identifiers[], bank_identification_status, <campos SEPA>, warnings[], errors[], data_freshness}` |
| `getSepaParticipation(bic)` | Solo los campos SEPA |
| `searchByName(texto, {country?, limit?})` | `{query, total, results:[{name, country_code, kind: "bic"|"code", ref, starts}]}` — coincidencia de todas las palabras, sin acentos; máx. 100 |
| `getStatus()` | `{engine_version, data_version, schwifty, checked, sources{}, source_status{}, conflicts}` |
| `getCoverage(país?)` | Métricas de cobertura de un país o de todos |
| `listCountries()` | Por prefijo IBAN: `{prefix, iso, name, directory, code_type, bank_code_length, branch_code_length, lookup_branch, bank_code_alpha}` |

## Resultado de identificación

| Campo | Tipo | Significado |
|---|---|---|
| `engine_version` | string | Versión del motor |
| `lookup_timestamp` | ISO 8601 | Momento de la consulta (en el navegador) |
| `country_code`, `country_name{en,es}` | | País del IBAN (prefijo) |
| `iban_valid` | bool | Dígitos ISO correctos **y** control nacional no inválido |
| `iban_checksum_valid` | bool | Dígitos de control ISO 13616 (mod 97) |
| `iban_structure_valid` | bool | Longitud y formato BBAN del país |
| `national_check` | `VALID` / `INVALID` / `NOT_AVAILABLE` | Dígito de control nacional (15 países); `NOT_AVAILABLE` si el país no tiene uno verificado |
| `iban_formatted` | string | IBAN en grupos de 4 (solo en memoria, nunca se envía) |
| `national_bank_code`, `national_bank_code_type{en,es}`, `branch_code` | | Código nacional extraído según el SWIFT IBAN Registry |
| `bank_name`, `bank_legal_name`, `bank_city`, `lei` | | Datos de la entidad según la fuente |
| `bank_status` | `ACTIVE` / `DELETION_SCHEDULED` | `successor_code` si la fuente lo indica |
| `bic_candidates[]` | BIC11 | BIC relacionados |
| `bic_status` | `CONFIRMED` / `CANDIDATES` / `NONE` | |
| `bic_relation` | `OFFICIAL_LIST` / `LEI_CHAIN` / `BIC_PREFIX_CONVENTION` | Cómo se relacionó el BIC (`bank_source.relation` puede ser además `ECB_RIAD_CONVENTION`: entidad identificada por su código en la lista MFI del BCE) |
| `bank_identification_status` | ver abajo | |
| `bank_source{id, institution, license, attribution, url, relation}`, `bank_source_date` | | Trazabilidad del dato |
| `sct_participation_status`, `sct_inst_participation_status`, `sdd_core_participation_status`, `sdd_b2b_participation_status` | `REGISTERED` / `FUTURE` / `LEFT` / `NOT_REGISTERED` / `UNKNOWN` | Registro del EPC para el BIC (`UNKNOWN` si no hay BIC o no hay datos de ese esquema) |
| `sepa_bic`, `sepa_match` (`EXACT` / `HEAD_OFFICE` / `NONE`), `sepa_participant_name`, `sepa_dates{ESQUEMA:{readiness, leaving}}`, `epc_register_date` | | Detalle EPC |
| `warnings[]`, `errors[]` | códigos | Ver abajo |
| `data_freshness{data_version, checked, stale}` | | `stale = true` si la última comprobación tiene más de 3 días |

### `bank_identification_status`

| Valor | Cuándo |
|---|---|
| `IDENTIFIED` | El código está en un directorio oficial publicado |
| `IDENTIFIED_BY_BIC_PREFIX` | País cuyo código bancario es el prefijo BIC; entidad deducida de BIC registrados |
| `AMBIGUOUS` | Varias entidades comparten el código/prefijo |
| `NOT_FOUND` | Hay directorio y el código no figura (puede ser una entidad no incluida en la fuente) |
| `DIRECTORY_NOT_AVAILABLE` | No hay directorio público verificado para el país |
| `DIRECTORY_PENDING_LICENCE` | Existe directorio oficial pero su licencia está pendiente de verificar |
| `NOT_APPLICABLE` | El IBAN o el código no tienen un formato válido |

### Errores

`INCOMPLETE`, `WRONG_LENGTH`, `INVALID_CHARACTERS`, `TOO_LONG`, `UNSUPPORTED_COUNTRY`, `WRONG_STRUCTURE`, `CHECKSUM`, `NATIONAL_CHECK`, `CODE_FORMAT`, `BIC_FORMAT`, `DATA_LOAD`.

### Avisos

| Código | Texto para el usuario (ES) |
|---|---|
| `IBAN_VALID_NOT_ACCOUNT_EXISTENCE` | Un IBAN válido no prueba que la cuenta exista ni quién es su titular. |
| `NATIONAL_CHECK_NOT_AVAILABLE` | Este país no tiene un dígito de control nacional verificable. |
| `IDENTIFICATION_FROM_INVALID_IBAN` | El IBAN no es válido; la entidad mostrada corresponde al código, pero puede haber un error de escritura. |
| `BIC_CANDIDATE_NOT_CONFIRMED` | BIC candidato obtenido por el LEI de la entidad; no confirmado por la fuente oficial. |
| `ECB_RIAD_CONVENTION` | Entidad identificada por su código en la lista oficial de entidades del BCE (FR, MC, LU, GR); solo entidades de crédito. |
| `BIC_PREFIX_CONVENTION` | BIC deducido de que el código bancario coincide con el prefijo BIC. |
| `DIRECTORY_PARTIAL` | El directorio no incluye todas las entidades (p. ej., entidades de pago). |
| `FALLBACK_SOURCE` | Datos de la copia del directorio oficial incluida en schwifty (la descarga directa no estaba disponible). |
| `SOURCE_CONFLICT` | Las fuentes no coinciden; se muestra la de mayor prioridad. |
| `CODE_DELETION_SCHEDULED` | La fuente anuncia la baja del código. |
| `REACHABILITY_NOT_GUARANTEED` | Estar inscrito en el EPC no garantiza que una transferencia concreta llegue. |
| `FUTURE_PARTICIPATION` | La adhesión tiene fecha futura. |
| `SEPA_MATCH_HEAD_OFFICE` | Participación encontrada para la oficina principal (BIC8 + XXX). |
| `TEST_BIC` | BIC de pruebas (8.º carácter "0"). |
| `DATA_STALE` | Los datos tienen más de 3 días sin comprobar. |

## Versionado

- `engine_version` sigue SemVer. Campos nuevos = versión menor; cambios de significado = versión mayor.
- `meta.schema` (hoy 2) es la versión del formato de `data/v2`; un cambio incompatible publicará `data/v3` en paralelo.
- `meta.data_version` es un hash del contenido publicado: cambia solo si cambian los datos.

## Limitaciones explícitas

El motor no verifica titulares (VoP), no comprueba que la cuenta exista, no garantiza el enrutamiento y no consulta SwiftRef. La participación EPC es una inscripción declarada en un registro, no una prueba de alcanzabilidad operativa.
