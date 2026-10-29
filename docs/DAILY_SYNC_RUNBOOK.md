# Runbook de la sincronización diaria

## Qué ocurre cada día

GitHub Actions (`.github/workflows/main.yml`) se ejecuta a las 05:17 UTC (GitHub puede retrasarlo) y también con cada push a `main` y manualmente ("Run workflow").

1. **test**: dependencias fijadas, `pip-audit`, pruebas Python y JavaScript.
2. **sync**: `python -m sepa_tools sync`
   - cada fuente: petición condicional → si no cambió, nada; si cambió, parseo → control de calidad → instantánea;
   - fusión → publicación atómica de `data/v2` → ficheros de compatibilidad → matriz de cobertura;
   - commit **solo si cambian los datos**;
   - construcción de la web y subida a Pages;
   - `check-run` y `selftest`: si algo falla, el paso queda en rojo y GitHub envía un correo.
3. **deploy**: publica la web aunque haya avisos (con los últimos datos buenos).

Frecuencia real de las fuentes: EPC semanal; Banco de España, OeNB, BCE diaria; Bundesbank trimestral; GLEIF BIC-LEI mensual. El sistema **comprueba** a diario; no afirma que todo cambie a diario.

## Cómo comprobar que funciona

- Pestaña **Actions**: una ejecución diaria en verde.
- `https://<dominio>/tools/data/v2/status.json`: `checked` es de hoy y cada fuente tiene `status` `unchanged` o `updated`.
- En la web, el pie muestra "Datos actualizados el …"; los datos de más de 3 días generan el aviso `DATA_STALE` en los resultados.
- `docs/SEPA_41_COUNTRIES_COVERAGE.md` en el repositorio refleja la última versión publicada.

## Errores y qué hacer

| Síntoma (en el log o `state/last_run.json`) | Causa probable | Acción |
|---|---|---|
| `FetchError: HTTP 5xx`, timeout | Fuente caída | Nada: se conservan los datos; se reintenta al día siguiente. Si dura más de una semana, revisar la URL en el registro. |
| `HTTP 401/403` | La fuente exige registro o bloquea | No eludir. Buscar URL pública alternativa o marcar la fuente como `RESTRICTED`. |
| `cabecera ... inesperada`, `línea con longitud inesperada` | Cambió el formato | Actualizar el conector y añadir un fixture con el nuevo formato a `tests/make_source_fixtures.py`. |
| `bloqueado por control de calidad: desaparecerían N de M` | Fichero incompleto o cambio masivo real | Descargar el fichero a mano y comparar. Si el cambio es real, subir `max_drop_ratio` de esa fuente en el registro para una ejecución y volver a bajarlo. |
| `banks/XX.json: pasaría de N a M códigos` | Validación final de publicación | Igual que el anterior. Para retirar un país a propósito, borrar `data/v2/banks/XX.json` en un PR revisado. |
| `canario ... no encontrado / nombre inesperado` | Cambio en la fuente o error de parseo | Revisar la instantánea de la fuente en `state/snapshots/`. |
| `no se encuentra el enlace ...` (Bundesbank, BCE) | Cambió la página de descargas | Ajustar la expresión regular del conector. Mientras tanto, Alemania usa la copia de schwifty. |

## Recuperación

- **Volver a la versión anterior de los datos**: `git revert <commit "Datos SEPA Tools actualizados ...">` y push; o restaurar `data/v2` y `state/` desde un commit anterior.
- **Repetir una ejecución**: Actions → "Run workflow".
- **Ejecución local sin red** (diagnóstico): `python -m sepa_tools sync --offline`.
- **Forzar la descarga de una fuente**: borrar su entrada en `state/sources_state.json` (sha256/etag) y ejecutar.

## Política de reintentos

3 intentos por descarga con espera creciente (5 s, 10 s, 15 s); en 429 espera 30 s × intento; 401/403 no se reintenta. La API LEI de GLEIF se consulta en lotes de 100 con 1 s entre peticiones y solo para LEI nuevos.

## Pausa de GitHub por inactividad

GitHub desactiva los workflows programados de repositorios sin actividad en 60 días. Los commits de datos lo evitan normalmente; si ocurre, Actions → "Enable workflow".
