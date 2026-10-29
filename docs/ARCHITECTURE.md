# Arquitectura — SEPA Tools 2.0

## Decisión: static-first (alternativa A)

| Criterio | A · Estática (elegida) | B · Backend API | C · Híbrida |
|---|---|---|---|
| Coste | 0 € (GitHub Actions + Pages / hosting actual) | servidor + BD | parte de B |
| Privacidad | el IBAN no sale del navegador | el IBAN viaja al servidor | según el caso |
| Mantenimiento | sin servidores, sin parches de SO | servidor 24/7, copias, monitorización | ambos |
| Rendimiento | CDN, JSON cacheables (≤ 600 KB por país) | latencia de API | — |
| Licencias | solo se publican datos con licencia verificada | igual | igual |

Todos los datos que necesita la consulta son públicos, pequeños (≈ 2 MB en total, troceados por país) y cambian como mucho a diario, así que un backend no aporta nada que justifique su coste ni el riesgo de recibir IBAN. Si en el futuro se publican fuentes con restricciones de redistribución (no permitido hoy), la alternativa C permitiría consultarlas en servidor enviando solo país + código bancario.

## Componentes

```mermaid
flowchart LR
  subgraph Fuentes oficiales
    EPC[EPC: SCT, SCT Inst, SDD Core, SDD B2B]
    BDE[Banco de España: lista IFM]
    BBK[Bundesbank: Bankleitzahlendatei]
    OENB[OeNB: SEPA-Verzeichnis]
    CNB[ČNB: códigos bancarios]
    ECB[BCE: lista MFI]
    GLEIF[GLEIF/SWIFT: BIC-LEI + API LEI]
    SCH[schwifty: registro IBAN SWIFT + copias de directorios]
  end
  subgraph GitHub Actions diario
    C[connectors/*] --> Q[quality.gate]
    Q --> SN[(state/snapshots)]
    SN --> M[merge.build]
    M --> P[publish atómico]
    P --> D[(data/v2)]
    D --> S[site/build_site.py]
  end
  Fuentes oficiales --> C
  S --> W[/tools ES/EN + data/v2/]
  W --> B[Navegador: sepa-engine.js]
```

| Componente | Fichero | Responsabilidad |
|---|---|---|
| Registro de fuentes | `DATA_SOURCES_REGISTRY.yaml`, `sepa_tools/sources.py` | Licencia, condiciones, prioridad, `publish`. Rechaza `publish: true` con licencias no verificadas. |
| Países | `reference/sepa_countries.json`, `sepa_tools/countries.py` | 41 países SEPA + Gibraltar, territorios (JE/GG/IM→GB, AX→FI, DOM→FR), tipos de código. |
| Especificaciones IBAN | `sepa_tools/ibanspec.py` | API pública de schwifty (registro IBAN de SWIFT). Posiciones de banco, oficina, control. |
| Descarga | `sepa_tools/http.py` | Reintentos con espera, peticiones condicionales (ETag/Last-Modified), sha256, límite de tamaño. No reintenta 401/403. |
| Conectores | `sepa_tools/connectors/` | Parseo y normalización por fuente. |
| Calidad | `sepa_tools/quality.py` | Mínimo de registros, bajas masivas (> 15 %) bloqueadas, diff de altas/bajas/modificaciones. |
| Fusión | `sepa_tools/merge.py` | Prioridades, fallbacks, BIC confirmado/candidato, conflictos, contraste BCE, índices. |
| Publicación | `sepa_tools/publish.py` | Escritura en `data/v2.tmp`, validación, sustitución atómica; nunca deja datos a medias. |
| Cobertura | `sepa_tools/coverage.py` | Métricas reales y `docs/SEPA_41_COUNTRIES_COVERAGE.md`. |
| Compatibilidad | `sepa_tools/legacy.py` | `participants.json`, `changes.json`, `status.json` con el formato original. |
| Controles | `sepa_tools/selftest.py` | Canarios sobre datos reales tras cada sincronización. |
| Motor web | `web/engine/sepa-engine.js` | Validación IBAN (mod 97 + control nacional de 15 países, equivalente a schwifty), extracción, resolución, BIC, nombre, SEPA. |
| Web | `site/` | Páginas estáticas SEO ES/EN, interfaz de las herramientas. |

## Flujo de datos

1. Cada conector descarga su fuente (condicional) y produce observaciones normalizadas con `src`.
2. `quality.gate` compara con la instantánea anterior; si falla, se conserva la anterior y se registra el error.
3. `merge.build` elige por país la fuente de mayor prioridad con datos (las de `fallback_for` solo si falta la principal), calcula BIC y estados, y genera índices.
4. `publish` escribe `data/v2` de forma determinista (sin cambios → mismos bytes → sin commit).
5. `site/build_site.py` genera las páginas y copia `data/v2` a `/tools/data/v2/`.
6. En el navegador, `sepa-engine.js` descarga solo `iban-specs.json`, `banks/<PAÍS>.json`, `sepa.json` y, si hace falta, `names.json`/`bic8.json`.

## Decisiones

- **schwifty como motor de especificaciones IBAN** (no se reimplementa el registro de SWIFT). En el navegador se replican los algoritmos con pruebas cruzadas contra schwifty (2.643 casos, 42 prefijos).
- **Los datos bancarios de schwifty no se usan por defecto**: solo los ficheros `generated_*` cuya fuente original es oficial; los de España (iban.es), Italia (ibancalculator.com), Rumanía (web de terceros) y los `manual_*` están excluidos. Alemania, Austria y República Checa usan la copia de schwifty solo como respaldo de la descarga directa.
- **BIC confirmado vs candidato**: confirmado solo si la fuente oficial relaciona código y BIC. Por LEI (código oficial → LEI → BIC GLEIF/SWIFT) o por convención de prefijo BIC se publica como candidato.
- **Países con código = prefijo BIC** (GB, IE, NL, BG, RO, MT, GI, LV): la entidad se deduce de BIC registrados en el EPC y en GLEIF; estado `IDENTIFIED_BY_BIC_PREFIX` y `AMBIGUOUS` si hay varias entidades.
- **El BCE no se usa para mapear códigos de IBAN** (el RIAD es un identificador estadístico); solo contrasta entidades por LEI y, en España, por RIAD = "ES"+código.
- **Ficheros públicos deterministas**; la hora de comprobación va en `data/v2/status.json` (no versionado).

## Limitaciones

- Directorios publicados hoy: los que tienen licencia verificada (ver matriz de cobertura). 12 países tienen directorio oficial importable pero sin publicar hasta revisar su licencia.
- España: la lista IFM del Banco de España cubre entidades de crédito y banco central, no entidades de pago ni de dinero electrónico.
- Alemania: el control nacional depende de ~150 métodos por BLZ y no se aplica (se indica "no disponible").
- La participación EPC no es enrutamiento operativo ni garantiza la aceptación de una transferencia.
