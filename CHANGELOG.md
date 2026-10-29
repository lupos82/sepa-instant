# Changelog

## 2.1.0 — 2026-10-29

- 12 países más con directorio (BE, CH, LI, FI, HR, HU, LT, NO, PL, SE, SI, SK) por aceptación de riesgo documentada del COO.
- Francia, Mónaco, Luxemburgo y Grecia: entidades identificadas por su código RIAD en la lista MFI del BCE (`ECB_RIAD_CONVENTION`, con aviso; solo entidades de crédito; sin páginas por código).
- BIC candidatos por LEI: se priorizan los inscritos en el EPC y se descartan los de pruebas o pasivos que no figuran en el EPC.
- Correcciones de fuentes: nueva cabecera del Banco de España, Accept de GLEIF, fecha del Bundesbank.
- 28 países con identificación del banco (antes 12).

## 2.0.0 — 2026-10-28 (rama `sepa-tools-2.0`, pendiente de revisión)

### Añadido
- Motor de datos `sepa_tools` (Python): registro de fuentes y licencias, conectores (EPC SCT/SCT Inst/SDD Core/SDD B2B, Banco de España, Bundesbank, OeNB, ČNB, BCE, GLEIF BIC-LEI y API LEI, copias de directorios de schwifty), controles de calidad, fusión con prioridades y conflictos, publicación atómica en `data/v2`, historial de cambios, matriz de cobertura, canarios (`selftest`).
- Motor web `sepa-engine.js`: validación IBAN de 41 países + GI con control nacional, identificación por IBAN, por código, por BIC y por nombre, participación en 4 esquemas EPC, avisos y estado de frescura de datos.
- Web ES/EN en `/tools/` (14.738 páginas): identificar banco por IBAN, validar IBAN, código bancario, BIC, SEPA Instant, fichas de entidad, guías y fuentes/licencias. Resultado en 4 secciones.
- Documentación (`docs/`), paquete de integración para la web corporativa (`integration/`), pruebas Python, JavaScript y Playwright.
- Workflow: pruebas en PR; en `main`, sincronización diaria con commit solo si cambian los datos, avisos por correo si una fuente o canario falla.

### Cambiado
- `index.html` (herramienta original): el parámetro `?q=` ya no acepta valores con forma de IBAN.
- `participants.json` / `changes.json` / `status.json` se generan ahora desde el motor 2.0 con el mismo formato.
- `README.md` reescrito.

### Corregido respecto al paquete SEO anterior
- El paquete SEO entregado antes (`paquete-seo-para-gpt.zip`) publicaba códigos bancarios de España incluidos en schwifty, que proceden de iban.es y no del Banco de España. 2.0 los excluye: España se publica solo desde la lista IFM del Banco de España. **Si ese paquete llegó a publicarse en la web, debe sustituirse por esta versión.**
- Los textos ya no afirman que se identifica el banco "en la mayoría de países".

### Eliminado
- `sepa-instant-ficheros.zip` y `sepa-instant-reachability.zip` (paquetes de instalación antiguos, ya no necesarios).
