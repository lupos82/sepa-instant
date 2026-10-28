# Informe de pruebas

Ejecución: 28-10-2026, entorno de desarrollo aislado (Linux, Python 3.11, Node 22, Chromium/Playwright). Estas mismas pruebas se ejecutan en GitHub Actions en cada push, PR y ejecución diaria.

## Resumen

| Suite | Comando | Resultado |
|---|---|---|
| Python: conectores, fusión, calidad, sincronización, publicación, compatibilidad, especificaciones IBAN | `python -m pytest -q` | **64/64** |
| JavaScript: motor IBAN contra schwifty (41 países + GI) | `node --test tests/js/engine_iban.test.js` | **4/4** (2.643 casos IBAN) |
| JavaScript: identificación, BIC, nombre, SEPA, estado, datos obsoletos | `node --test tests/js/engine_lookup.test.js` | **13/13** |
| Navegador (Playwright): interfaz, privacidad, accesibilidad de teclado, móvil, SEO | `node tests/e2e/site.e2e.js` | **19/19** |
| Vulnerabilidades en dependencias | `pip-audit -r requirements.txt` | Sin vulnerabilidades conocidas |
| Determinismo de la web | dos generaciones con un minuto de diferencia | ficheros idénticos byte a byte |

## Qué cubren

**IBAN (41 países + Gibraltar).** Para cada prefijo, IBAN aleatorios válidos generados por schwifty y variantes alteradas (dígitos ISO, dígito nacional, longitud, caracteres, estructura). El motor JS debe coincidir con schwifty en validez, dígitos ISO, control nacional y extracción de código de banco y oficina. Incluye el control nacional de los 15 países que lo tienen verificado (ES, BE, FR, MC, IT, SM, FI, EE, PL, NO, PT, SI, ME, MK, RS). Prueba explícita de que el código bancario **no** se asume de 4 dígitos (longitudes 2 a 8 y alfabéticos).

**Sincronización** (con ficheros de prueba en el formato real de cada fuente):

| Escenario | Prueba |
|---|---|
| Fuente sin cambios | idempotencia: segunda ejecución sin cambios en ficheros versionados |
| Altas / modificaciones / bajas | diff por fuente en `changes_v2.json` |
| Fichero corrupto o formato cambiado | error registrado, datos anteriores intactos |
| Fichero incompleto / baja masiva | bloqueado por el control de calidad (> 15 %) |
| Fuente caída | se conserva la instantánea anterior |
| Respaldo (schwifty) | solo se usa sin datos de la fuente directa |
| Conflicto entre fuentes | prioridad + marca `SOURCE_CONFLICT` |
| Publicación fallida | `data/v2` no queda a medias (sustitución atómica) |
| Licencia no verificada con `publish: true` | el registro se rechaza |
| Baja programada (Bundesbank) | `DELETION_SCHEDULED` + sucesor |
| Contraste BCE | marca `m:1` |
| Compatibilidad | `participants.json`/`changes.json`/`status.json` con el formato de la herramienta actual |

**SEPA.** Estados `REGISTERED`, `FUTURE`, `LEFT`, `NOT_REGISTERED`, `UNKNOWN` (esquema sin datos descargados), coincidencia por oficina principal, BIC duplicados, cuatro esquemas.

**Web.** Las 4 secciones del resultado; ES/EN; país sin directorio; licencia pendiente; búsqueda por código con selector de país; BIC; nombre con tildes; **el IBAN no aparece en ninguna petición**, la URL no cambia, nada en `localStorage`/`sessionStorage`/cookies; `?q=` con IBAN ignorado; entrada maliciosa mostrada como texto; páginas probadas servidas con la Content-Security-Policy recomendada (`integration/tools.htaccess`) sin violaciones; redirección de idioma en `/tools/`; navegación por teclado; sin scroll horizontal a 390 px; páginas estáticas con contenido, `canonical` y `hreflang` sin JavaScript; sin errores de consola.

## Lo que NO se ha ejecutado aquí (y cómo se verificará)

- **Descargas reales de las fuentes oficiales.** El entorno de desarrollo no tiene acceso a esas webs. Los conectores se han probado con ficheros que reproducen el formato publicado de cada fuente. La primera ejecución de GitHub Actions descargará los datos reales; el paso `selftest` comprobará los canarios (CaixaBank 2100, Santander 0049, BBVA 0182, Bundesbank 10010010 / Commerzbank 37040044, OeNB 20111, ČNB 0800, ING/ABN AMRO, Barclays, AIB, y los BIC CAIXESBBXXX y COBADEFFXXX en SCT Inst) y marcará la ejecución en rojo si algo no cuadra.
- En el entorno sin red, `selftest` sobre los datos semilla evalúa 8 canarios y señala 1 (Barclays/GB), porque la semilla solo contiene SCT Inst y no el registro SCT ni el fichero GLEIF; se espera que desaparezca con la primera descarga real.
- España aparecerá con directorio publicado tras la primera descarga real del Banco de España (la semilla no la incluye porque los datos de España de schwifty están excluidos por licencia).
- No se ha medido rendimiento en producción; el mayor JSON por país pesa ~520 KB (Alemania) y se cachean.

## Cómo repetirlas

Ver la sección "Pruebas" de `README.md`. Las capturas de la interfaz se guardan en `tests/.tmp/shots/`.
