# Prompt para el hilo de GPT de la web cryptopocket.io

Copia todo lo que hay debajo de la línea y pégalo en el hilo. Adjunta también estos tres ficheros de la carpeta `integration/`: `INTEGRATION_WEB_CRYPTOPOCKET.md`, `INTEGRATION_MANIFEST.json` y `tools.htaccess`.

---

Hola. Necesito que integres en la web corporativa de Cryptopocket (repositorio `web-cryptopocket.io`, la que tú conoces: generación estática, GitHub Actions y hosting en DonDominio) la nueva versión de nuestras herramientas SEPA, **SEPA Tools 2.0**. Te adjunto la guía de integración (`INTEGRATION_WEB_CRYPTOPOCKET.md`), el manifiesto (`INTEGRATION_MANIFEST.json`) y el `.htaccess` para `/tools` (`tools.htaccess`). Léelos completos antes de empezar.

## Contexto

- SEPA Tools vive en otro repositorio: `https://github.com/lupos82/sepa-instant` (rama `main`). Allí, cada día a las 05:17 UTC, un workflow comprueba las fuentes oficiales (EPC, Banco de España, Bundesbank, OeNB, ČNB, BCE, GLEIF), valida los datos y los guarda en `data/v2`.
- Ese repositorio incluye un generador (`site/build_site.py`, Python 3.11+, solo biblioteca estándar) que crea unas 14.700 páginas en español e inglés bajo `/tools/` con: identificar el banco de un IBAN, validar IBAN de los 41 países SEPA, buscar por código bancario nacional, buscar BIC, consultar SEPA Instant, fichas de entidad, guías y una página de fuentes y licencias.
- El IBAN se procesa **solo en el navegador**: nunca se envía a ningún servidor, no va en la URL y no se guarda.
- Las páginas ya traen SEO completo: title y description únicos, canonical a `https://cryptopocket.io/tools/...`, hreflang es/en, JSON-LD, Open Graph, sitemaps (`/tools/sitemap.xml` es un índice).
- Importante: la versión 2.0 está en revisión en la rama `sepa-tools-2.0` de `sepa-instant`. Puedes preparar el PR de la web ya, pero no funcionará hasta que yo te confirme que está fusionada en `main`. Para probar antes, puedes usar `ref: sepa-tools-2.0` en el checkout y volver a `main` antes de fusionar.
- Una vez fusionada, habrá una copia de previsualización en `https://sepa.cryptopocket.io/tools/` con `noindex`. Puedes mirarla para ver cómo queda. La herramienta antigua `https://sepa.cryptopocket.io/` (y `?embed=1`) sigue funcionando y no hay que tocarla.

## Lo que te pido

1. **Integrar la generación de `/tools` en el workflow de la web**, exactamente como indica el §3 de la guía:
   - checkout de `lupos82/sepa-instant` (`main`) en `_sepa_tools`;
   - `python _sepa_tools/site/build_site.py` con `PUBLIC_BASE=https://cryptopocket.io`, `CONTACT_URL=<URL real de nuestra página de contacto>` y `OUT_DIR=<la carpeta de salida real de la web>`;
   - copiar `_sepa_tools/integration/tools.htaccess` a `<salida>/tools/.htaccess`;
   - añadir un `schedule` diario a las 06:10 UTC y `workflow_dispatch`, para que `/tools` se actualice aunque la web no cambie.
   Adapta los nombres de carpetas y pasos a cómo está montada nuestra web; no cambies el comportamiento del generador.
2. **Despliegue incremental en DonDominio** (§4): la primera subida son ~14.770 ficheros (~215 MB); las siguientes deben subir solo los ficheros cambiados. Si el despliegue actual sube todo cada vez, cámbialo a uno incremental con estado (por ejemplo `SamKirkland/FTP-Deploy-Action` o `lftp mirror -R --only-newer`) o despliega `/tools` con un paso incremental propio. Credenciales solo en GitHub Secrets.
3. **Enlazar las herramientas sin rediseñar nada** (§5): un enlace "Herramientas" → `/tools/es/` (y "Tools" → `/tools/en/` en inglés) en el menú o el pie, y la línea `Sitemap: https://cryptopocket.io/tools/sitemap.xml` en `robots.txt`.
4. **Retirar el paquete SEO anterior** si se llegó a integrar (`paquete-seo-para-gpt.zip`, la versión que te pasé antes): tenía códigos bancarios de España de una fuente no oficial. Esta versión 2.0 lo sustituye por completo (§9).
5. Pasar las **10 comprobaciones de aceptación** del §7 de la guía y decirme el resultado de cada una.

## Reglas que no se pueden saltar

- No rediseñes ni sustituyas la web corporativa. Fuera de `/tools/` solo cambian el enlace del menú/pie, `robots.txt` y el workflow.
- `/tools/` es propiedad del generador: se borra y se regenera entero en cada construcción. No guardes allí ficheros propios ni edites los HTML generados. Si quieres cambiar el aspecto de esas páginas para que encajen mejor con la web, propónmelo y lo haremos en `sepa-instant` (`site/site.css`, `site/build_site.py`).
- No añadas en `/tools` grabación de sesiones, mapas de calor con texto, captura de formularios ni formularios GET con IBAN. Si la web tiene analítica o banner de cookies, inyéctalos con `EXTRA_HEAD_FILE` / `EXTRA_BODY_END_FILE` y amplía la Content-Security-Policy del `.htaccess` solo con los dominios necesarios.
- No cambies los textos de avisos, fuentes ni atribuciones (son condiciones de licencia de las fuentes).
- No publiques otros datos bancarios en `/tools`.
- No dejes credenciales en el código ni en el frontend.
- No publiques en producción sin que yo lo revise: trabaja en una rama, abre un PR y dime qué ha cambiado. Si tu flujo publica al fusionar, espera a mi OK.

## Qué necesito que me devuelvas

1. El diff o PR del workflow y de los ficheros tocados, explicando cada cambio.
2. Cómo queda el despliegue (qué se sube la primera vez y qué se sube cada día).
3. El resultado de las 10 comprobaciones del §7 (con capturas o URL).
4. Lo que no hayas podido hacer y por qué (por ejemplo, si el hosting no admite alguna directiva del `.htaccess`: indícame cuál y coméntala, no la borres en silencio).
5. Los pasos manuales que me toquen a mí: enviar el sitemap en Google Search Console y Bing Webmaster Tools, confirmar la URL de contacto, etc.

Si algo de la guía no encaja con cómo está montada la web, pregúntame antes de improvisar.
