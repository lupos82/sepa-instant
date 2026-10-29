# Normalización, deduplicación y resolución de conflictos

## Importación

| Fuente | Reglas |
|---|---|
| EPC | Cabecera por nombre (no por posición). BIC normalizado a 11 caracteres (8 → +XXX); filas sin BIC válido descartadas; BIC repetido → primera fila. País EPC → ISO con `reference/sepa_countries.json` (si falta, país del BIC). Fechas a ISO. Se conservan las bajas (`LEFT`) en v2; el fichero de compatibilidad las omite como antes. |
| Bundesbank | Ancho fijo de 168 caracteres (latin-1). Se rechaza el fichero si una línea tiene longitud inesperada o el BLZ no es numérico. `Merkmal=1` = fila principal. `Hinweis auf Löschung=1` → `DELETION_SCHEDULED` con `Nachfolge-BLZ`. |
| OeNB | Se localiza la línea de cabecera `Kennzeichen;` tras el aviso. BLZ con relleno a 5 dígitos. Fila principal: `Hauptanstalt` o `Institutsart=KI`. |
| ČNB | Primera fila = cabecera si no empieza por 4 dígitos. Código de 4 dígitos como texto. |
| Banco de España | Solo "Entidad de crédito" y "Banco central" con "Código supervisor" de 4 dígitos (conserva ceros). Se registra si el RIAD es "ES"+código. |
| BCE | UTF-16 tabulado (gz). Solo entidades de crédito y bancos centrales. |
| GLEIF BIC-LEI | Solo BIC de países/territorios SEPA. |
| schwifty | Solo ficheros `generated_*` declarados; formatos v1 y v2. |

Normalización general: espacios múltiples a uno, sin espacios en BIC/LEI, mayúsculas en BIC/LEI/RIAD, **códigos siempre como texto** (nunca número), fechas ISO `AAAA-MM-DD`. Los nombres no se reescriben.

## Deduplicación

- Un código con varias filas (sucursales) se agrega en una entrada: se toma la fila principal; los BIC distintos se listan con el de la fila principal primero.
- En el índice de nombres, una entrada por (nombre normalizado, BIC8) o (nombre normalizado, país:código).
- **No se fusionan entidades distintas por compartir marca**: cada código y cada BIC son entradas separadas.

## Prioridad entre fuentes (por país)

1. Fuente de directorio publicable de menor `priority` con datos.
2. Las fuentes con `fallback_for` (copias de schwifty) solo si su fuente principal no tiene datos.
3. Si ninguna fuente de directorio publicable existe y el código bancario son 4 letras: derivación por prefijo BIC (EPC primero; nombres GLEIF si no está en el EPC).

## BIC

| Caso | Publicación |
|---|---|
| La fuente oficial da el BIC del código | `CONFIRMED` / `OFFICIAL_LIST` |
| Código oficial con LEI → BIC del país en el fichero GLEIF/SWIFT (preferencia XXX) | `CANDIDATES` / `LEI_CHAIN` |
| País con código = prefijo BIC | `CANDIDATES` / `BIC_PREFIX_CONVENTION`; `amb:1` si hay varias entidades con BIC8 y nombres distintos |
| Sin evidencia | sin BIC |

Nunca se deduce un BIC ni un banco por similitud de nombres.

## Conflictos

Si dos fuentes del mismo país dan BIC con distinto BIC8 para el mismo código: se mantiene el de la fuente prioritaria, se marca `x:1` en la entrada, se cuenta en `meta.conflicts` y se lista en `state/last_run.json` (ambas observaciones con su procedencia). Las observaciones de cada fuente se conservan en `state/snapshots`.

## Vigencia e histórico

- Cada fichero de país lleva `effective_date` (fecha de validez del Bundesbank, fecha del fichero OeNB, fecha de descarga para las fuentes diarias).
- Los cambios entre versiones (altas, bajas, modificaciones) se guardan por fuente y fecha en `state/changes_v2.json`; el historial completo está en git.
- Códigos con baja programada se publican con su sucesor hasta que la fuente los elimina.
- Un dato antiguo nunca sobrescribe uno actual: las fuentes de respaldo solo se usan sin datos de la principal.
