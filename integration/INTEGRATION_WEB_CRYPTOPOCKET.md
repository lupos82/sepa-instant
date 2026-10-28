# Integración de SEPA Tools 2.0 en cryptopocket.io/tools

Destinatario: quien mantiene el repositorio `web-cryptopocket.io` (generación estática, GitHub Actions, hosting en DonDominio).
Objetivo: servir las herramientas y sus ~14.700 páginas SEO en `https://cryptopocket.io/tools/` **sin rediseñar ni sustituir la web corporativa**.

## 1. Qué se integra

| Elemento | Origen | Destino en la web |
|---|---|---|
| Páginas ES/EN (HTML estático) | generadas por `site/build_site.py` del repo `lupos82/sepa-instant` | `/tools/es/…`, `/tools/en/…` |
| Datos públicos JSON | `data/v2/` del mismo repo (actualizado a diario) | `/tools/data/v2/…` |
| CSS/JS propios | `site/site.css`, `site/site.js`, `web/engine/sepa-engine.js` | `/tools/assets/…` |
| Sitemaps | generados | `/tools/sitemap.xml` (índice) + `/tools/sitemap-N.xml` |
| Raíz y 404 | generados | `/tools/index.html` (elige idioma), `/tools/404.html` |
| Reglas de servidor | `integration/tools.htaccess` | `/tools/.htaccess` |

Todo `/tools/` es **propiedad del generador**: se borra y se regenera completo en cada construcción. La web corporativa no debe guardar ficheros propios dentro de `/tools/`.

## 2. Arquitectura de la integración (recomendada)

```
lupos82/sepa-instant (main)                      web-cryptopocket.io
  05:17 UTC  sync diario → commit data/v2  ──▶   06:10 UTC (o tras su propio build)
                                                   checkout lupos82/sepa-instant
                                                   python site/build_site.py → <salida>/tools
                                                   copiar .htaccess
                                                   desplegar en DonDominio (solo cambios)
```

- El generador solo usa la biblioteca estándar de Python 3.11+ (no requiere `pip install`).
- Los datos se leen de `data/v2` ya validados y versionados en `main` de `sepa-instant`; la web **no** descarga fuentes oficiales.
- Salida determinista: si los datos no cambian, los ficheros generados son idénticos → el despliegue incremental no sube nada.

## 3. Paso a paso en el workflow de la web

Añadir al workflow existente, **después** de construir la web corporativa y **antes** del paso de despliegue (ajustar `DIST` a la carpeta de salida real):

```yaml
      - name: SEPA Tools — obtener generador y datos
        uses: actions/checkout@v4
        with:
          repository: lupos82/sepa-instant
          ref: main
          path: _sepa_tools
          fetch-depth: 1

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: SEPA Tools — generar /tools
        env:
          PUBLIC_BASE: https://cryptopocket.io
          CONTACT_URL: https://cryptopocket.io/contact      # ← URL real de contacto
          OUT_DIR: ${{ github.workspace }}/DIST              # ← carpeta de salida de la web
        run: |
          python _sepa_tools/site/build_site.py
          cp _sepa_tools/integration/tools.htaccess "$OUT_DIR/tools/.htaccess"
          test -f "$OUT_DIR/tools/es/index.html" && test -f "$OUT_DIR/tools/data/v2/iban-specs.json"
```

Y añadir disparadores para que `/tools` se refresque aunque la web no cambie:

```yaml
on:
  schedule:
    - cron: "10 6 * * *"     # después de la sincronización de sepa-instant (05:17 UTC)
  workflow_dispatch: {}
```

Opcional: `EXTRA_HEAD_FILE` / `EXTRA_BODY_END_FILE` apuntando a fragmentos HTML de la web (p. ej., banner de cookies). Ver §6.

## 4. Despliegue en DonDominio

- Primera subida: ~14.770 ficheros, ~215 MB. Siguientes: solo los cambiados (normalmente `data/v2/status.json` y las páginas cuyos datos cambien).
- Usar un despliegue **incremental** con estado, por ejemplo `SamKirkland/FTP-Deploy-Action` (guarda `.ftp-deploy-sync-state.json` en el servidor) o `lftp mirror -R --only-newer --parallel=4` si se usa SFTP/FTPS.
- Las credenciales FTP/SFTP deben estar en **GitHub Secrets** del repo de la web; nunca en el código ni en el frontend.
- Si el despliegue actual borra todo y sube todo, cambiarlo a incremental antes de integrar `/tools` (o excluir `/tools/` de ese paso y desplegarlo con uno incremental propio).
- Comprobar que el hosting sirve `.json` como `application/json` y respeta `.htaccess` (Apache).

## 5. Enlaces desde la web corporativa (sin rediseño)

Mínimo necesario:
1. Un enlace en el menú o el pie: "Herramientas" → `/tools/es/` (y "Tools" → `/tools/en/` en la versión inglesa).
2. `robots.txt` de la web: añadir `Sitemap: https://cryptopocket.io/tools/sitemap.xml`. No bloquear `/tools/`.
3. Si la web tiene su propio sitemap índice, puede incluir `https://cryptopocket.io/tools/sitemap.xml` o dejarlo separado.

Las páginas de `/tools` tienen su propia cabecera y pie con la marca Cryptopocket, enlace a la portada y botón de contacto. Para cambios visuales de esas páginas (colores, tipografía, cabecera), hacer un PR en `lupos82/sepa-instant` (`site/site.css`, `site/build_site.py`); **no editar los HTML generados**, porque se sobrescriben a diario.

## 6. Reglas obligatorias

| Regla | Motivo |
|---|---|
| No añadir en `/tools` grabación de sesiones, mapas de calor con texto ni captura de formularios | El IBAN no debe salir del navegador. Los campos llevan `data-private`, `data-hj-suppress`, `data-clarity-mask`, `ph-no-capture`. |
| No añadir parámetros de URL con el IBAN ni formularios GET propios | Privacidad |
| No modificar ni reescribir los textos de avisos y fuentes | Exactitud y condiciones de licencia (atribuciones) |
| No publicar otros datos bancarios en `/tools` | Solo se publican fuentes con licencia verificada |
| No cachear los HTML más de unas horas en CDN | Los datos pueden cambiar a diario |
| Mantener la página `/tools/{es|en}/fuentes-y-licencias/` enlazada desde el pie | Obligación de atribución de varias fuentes |
| Si se inyecta analítica con `EXTRA_HEAD_FILE`, ampliar la CSP del `.htaccess` solo con los dominios necesarios | Seguridad |

## 7. Comprobaciones de aceptación

1. `https://cryptopocket.io/tools/` redirige a `/tools/es/` o `/tools/en/` según el idioma del navegador.
2. `https://cryptopocket.io/tools/es/identificar-banco-iban/`: introducir `DE89 3704 0044 0532 0130 00` → IBAN válido, Commerzbank, BIC `COBADEFFXXX`, estado SEPA, fuente Bundesbank.
3. `https://cryptopocket.io/tools/en/iban-checker/france/`: un IBAN francés válido muestra "No bank directory available for this country" y el código extraído (comportamiento correcto: no hay directorio público para Francia).
4. Herramientas del navegador → Red: ninguna petición contiene el IBAN; solo `/tools/data/v2/*.json`.
5. `https://cryptopocket.io/tools/data/v2/status.json` → `checked` de hoy (o de ayer antes de las 06:10 UTC).
6. Ver código fuente de `/tools/es/codigo-banco/alemania/37040044/`: `<link rel="canonical" href="https://cryptopocket.io/tools/es/codigo-banco/alemania/37040044/">` y `hreflang` en.
7. `https://cryptopocket.io/tools/sitemap.xml` devuelve un `sitemapindex` y sus hijos cargan.
8. Una URL inexistente bajo `/tools/` devuelve 404 con la página bilingüe.
9. La consola del navegador no muestra errores ni violaciones de CSP.
10. La web corporativa (fuera de `/tools`) no ha cambiado salvo el enlace y `robots.txt`.

## 8. Relación con sepa.cryptopocket.io

- `https://sepa.cryptopocket.io/` (herramienta original) sigue funcionando igual, incluido `?embed=1`.
- `https://sepa.cryptopocket.io/tools/` es una **copia de previsualización** con `noindex` (para revisar cambios antes de que lleguen a la web). No enlazarla públicamente.
- Si un iframe de la web usa `https://sepa.cryptopocket.io/?embed=1`, puede mantenerse; las páginas nuevas de `/tools` son la opción recomendada para SEO.

## 9. Sustitución del paquete SEO anterior

Si se integró el paquete `paquete-seo-para-gpt.zip` (versión anterior), retirarlo y usar este procedimiento: aquel paquete incluía códigos de España de una fuente no oficial. Las rutas principales de `/tools/…` (portadas, validar IBAN, SEPA Instant, fichas de entidad, guías) usan los mismos slugs; las páginas que ya no se publican devolverán 404, que es lo correcto para datos no verificados. Revisar en Search Console tras el cambio.

## 10. Soporte

- Fallos de datos: Actions de `lupos82/sepa-instant` (correo automático de GitHub) y `docs/DAILY_SYNC_RUNBOOK.md`.
- Contrato del motor JS (si la web quiere usarlo en otras páginas): `docs/API_CONTRACT.md`.
