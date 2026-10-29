# Seguridad y privacidad

## Principio

El IBAN es un dato personal cuando identifica la cuenta de una persona física. SEPA Tools está diseñado para **no recibirlo nunca**: toda la validación e identificación ocurre en el navegador del usuario sobre datos públicos ya descargados.

## Medidas aplicadas

| Requisito | Cómo se cumple | Verificación |
|---|---|---|
| No almacenar IBAN completos | No hay servidor ni base de datos. El motor no usa `localStorage`/`sessionStorage`/cookies para IBAN (solo el idioma, en la herramienta antigua). | Revisión de código; prueba e2e "sin peticiones con el IBAN" |
| No poner IBAN en URLs | Los formularios no usan `GET`; el resultado no modifica la URL. El parámetro `?q=` de precarga **ignora** cualquier valor con forma de IBAN (web nueva y `index.html`). | e2e: `?q=<IBAN>` no rellena el campo; la URL no cambia tras consultar |
| No enviar IBAN a analítica | Las páginas no incluyen analítica. Los campos llevan `data-private`, `data-hj-suppress`, `data-clarity-mask="true"` y `ph-no-capture` para que herramientas de grabación habituales los oculten si la web corporativa las añade. | e2e: ninguna petición de red contiene el IBAN ni su código |
| No incluir datos bancarios personales en logs | No hay logs de consultas (no hay servidor). Los logs de sincronización solo contienen datos públicos de entidades. | — |
| Nada de credenciales en frontend | No hay claves ni tokens; los JSON son públicos. | `grep` en la salida de la web |
| No publicar datasets restringidos | `sources.py` impide `publish: true` con licencias `UNKNOWN`, `RESTRICTED`, `EXCLUDED` o `VERIFIED_INTERNAL_ONLY`; las fuentes no publicables no generan ficheros en `data/v2` ni en `state/snapshots`. | `test_registry_rejects_publish_with_unverified_licence` |
| Sin archivos confidenciales en GitHub | El repositorio solo contiene código, datos públicos y documentación. `.cache/` (descargas brutas) está en `.gitignore`. | — |
| Entrada controlada | IBAN ≤ 64 caracteres; código ≤ 16; nombre ≤ 80; todo lo mostrado se escapa (`textContent`/escape HTML). | Pruebas de entrada maliciosa (e2e) |
| Peticiones de la web | Solo al mismo origen (`/tools/data/v2/…`), `fetch` sin credenciales. Fuentes de Google Fonts en CSS. | e2e |

## Cadena de suministro

- Dependencias fijadas: `schwifty==2026.10.1`, `PyYAML==6.0.3` (producción); `pytest`, `pip-audit` (desarrollo); `playwright@1.48.2` solo en pruebas.
- `pip-audit` en cada ejecución del workflow.
- Las descargas de las fuentes se validan (formato, mínimos, bajas masivas) antes de publicarse; un fichero corrupto o manipulado no reemplaza los datos buenos.
- `sha256` de cada fichero descargado en `state/sources_state.json`.
- El workflow tiene permisos mínimos para publicar (`contents`, `pages`, `id-token`); no usa secretos.

## Recomendaciones para la web corporativa

1. Si se añade analítica o un gestor de etiquetas en `/tools`, **no** activar grabación de sesiones, mapas de calor con texto ni captura de formularios; respetar los atributos `data-private`.
2. Cabeceras recomendadas en el hosting: `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: https://cryptopocket.io; connect-src 'self'; frame-ancestors 'self'` (ajustar si la web añade scripts), `Referrer-Policy: strict-origin-when-cross-origin`, `X-Content-Type-Options: nosniff`.
3. No registrar el cuerpo de las peticiones ni las cadenas de consulta en los logs del servidor (no deberían contener IBAN, pero es una buena práctica).
4. La política de privacidad puede indicar: "Las herramientas de /tools procesan el IBAN exclusivamente en tu navegador; Cryptopocket no lo recibe ni lo almacena".

## Riesgos residuales

- Extensiones del navegador del usuario pueden leer lo que escribe (fuera de nuestro control).
- Si la web corporativa inyecta scripts de terceros en `/tools`, esos scripts tendrán acceso al DOM: deben revisarse.
- La exactitud depende de las fuentes oficiales; los avisos lo explican al usuario.
