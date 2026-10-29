# SEO — SEPA Tools 2.0

## Estrategia

Captar búsquedas informativas y transaccionales de todo el mundo ("de qué banco es este IBAN", "validar IBAN Alemania", "BLZ 10010010", "¿acepta mi banco SEPA Instant?", "BIC de …") con herramientas útiles y páginas con contenido real en HTML, en español e inglés, bajo `cryptopocket.io/tools/`, y llevar ese tráfico al contacto de Cryptopocket.

Regla de calidad: **solo se generan páginas de datos verificados**. No hay páginas de códigos de países sin directorio publicado, ni de códigos deducidos por prefijo BIC, ni de fuentes pendientes de licencia.

## Páginas generadas (con los datos actuales)

| Tipo | ES | EN | Nº por idioma | Intención de búsqueda |
|---|---|---|---|---|
| Portada de herramientas | `/tools/es/` | `/tools/en/` | 1 | herramientas IBAN/SEPA |
| Identificar banco por IBAN | `/tools/es/identificar-banco-iban/` | `/tools/en/iban-bank-lookup/` | 1 | "de qué banco es un IBAN", "IBAN bank lookup" |
| Validar IBAN + por país | `/tools/es/validar-iban/{país}/` | `/tools/en/iban-checker/{country}/` | 43 | "validar IBAN Alemania", "IBAN checker France" |
| Código bancario + por país + por código | `/tools/es/codigo-banco/{país}/{código}/` | `/tools/en/bank-code-lookup/{country}/{code}/` | ≈ 4.430 (+ España tras la primera descarga real) | "BLZ 37040044", "código entidad 2100", "bank code 20111" |
| Buscar BIC | `/tools/es/buscar-bic/` | `/tools/en/bic-lookup/` | 1 | "buscar BIC", "SWIFT code lookup" |
| SEPA Instant + por país | `/tools/es/sepa-instant/{país}/` | `/tools/en/sepa-instant/{country}/` | 42 | "bancos SEPA Instant Alemania" |
| Ficha de entidad (BIC inscrito en el EPC) | `/tools/es/banco/{bic}/` | `/tools/en/bank/{bic}/` | 2.843 (crecerá con SCT/SDD) | "CAIXESBBXXX", "BIC Commerzbank SEPA Instant" |
| Guías | `/tools/es/guias/{slug}/` | `/tools/en/guides/{slug}/` | 6 | qué es SEPA Instant, reglamento de pagos inmediatos, VoP, SCT vs SCT Inst, cómo saber si un banco acepta SEPA Instant, cómo saber de qué banco es un IBAN |
| Fuentes y licencias | `/tools/es/fuentes-y-licencias/` | `/tools/en/sources-and-licences/` | 1 | confianza (E-E-A-T) |

Total actual: **14.738 páginas** (ES + EN). Las páginas de códigos se paginan por país en índices de 500.

## Elementos técnicos en cada página

- `<title>` y `meta description` únicos, por idioma, con el dato concreto (código, entidad, país).
- `canonical` absoluto a `https://cryptopocket.io/tools/...` (configurable con `PUBLIC_BASE`).
- `hreflang` es/en + `x-default` (inglés) en HTML y en el sitemap.
- Datos estructurados JSON-LD: `WebApplication` (herramientas), `FAQPage` (preguntas frecuentes), `BreadcrumbList`, `Article` (guías) y `BankOrCreditUnion` (fichas de entidad y de código) según la página.
- Open Graph y Twitter Card.
- Contenido visible sin JavaScript (las herramientas mejoran la página, no la sustituyen).
- Enlazado interno: país ↔ códigos ↔ entidad ↔ SEPA ↔ guías; migas de pan.
- `sitemap.xml` (índice) → `sitemap-1.xml`, `sitemap-2.xml`… (10.000 URL por fichero) con `lastmod` = fecha del último cambio de datos.
- Salida determinista: si los datos no cambian, las páginas no cambian (no se "refresca" `lastmod` artificialmente).
- Rendimiento: HTML ligero, 1 CSS y 2 JS propios con caché por hash, JSON por país bajo demanda, sin dependencias de terceros salvo Google Fonts.
- Accesibilidad: navegación por teclado, `aria-live` en resultados, contraste AA, modo oscuro, sin scroll horizontal en móvil.

## Textos y mensajes

- Prudentes y exactos: "un IBAN válido no prueba que la cuenta exista", "estar inscrito en el EPC no garantiza que una transferencia llegue", "BIC candidato (no confirmado)".
- Nada de "100 %", "todos los bancos" ni "en tiempo real".
- Fuente y fecha en cada dato.

## Configuración para la web corporativa

| Variable | Valor recomendado |
|---|---|
| `PUBLIC_BASE` | `https://cryptopocket.io` |
| `CONTACT_URL` | URL real de la página de contacto (por defecto `https://cryptopocket.io/contact`) |
| `NOINDEX` | vacío en la web corporativa; `1` en la copia de previsualización de GitHub Pages |
| `EXTRA_HEAD_FILE`, `EXTRA_BODY_END_FILE` | HTML de la web (banner de cookies, analítica sin captura de formularios) |

## Pasos tras publicar

1. Google Search Console y Bing Webmaster Tools: enviar `https://cryptopocket.io/tools/sitemap.xml`.
2. Añadir `Sitemap: https://cryptopocket.io/tools/sitemap.xml` al `robots.txt` de la web.
3. Enlazar `/tools/es/` y `/tools/en/` desde el menú o el pie de la web corporativa.
4. Mantener `sepa.cryptopocket.io/tools/` con `noindex` (ya configurado) para evitar contenido duplicado. La herramienta antigua (`sepa.cryptopocket.io/`) puede seguir igual o redirigir a `/tools/es/sepa-instant/`.
5. Revisar en Search Console a las 2–4 semanas: páginas indexadas, consultas, CTR; ajustar títulos de las páginas con más impresiones.

## Riesgos

- Muchas páginas de código con plantilla parecida pueden indexarse lentamente; cada una tiene datos únicos (entidad, BIC, ciudad, fuente, SEPA) y enlaces internos útiles. Si Search Console muestra "rastreada, no indexada" en masa, priorizar la indexación de índices por país y fichas con BIC.
- Si una fuente deja de publicarse, sus páginas desaparecen en la siguiente generación (devolverán 404). Es preferible a mostrar datos no verificables.
