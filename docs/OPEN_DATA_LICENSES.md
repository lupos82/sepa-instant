# Licencias de datos abiertos

Revisión documental del 28-10-2026. **No es asesoramiento jurídico**: se recomienda que el equipo legal de Cryptopocket confirme las fuentes marcadas como "revisión recomendada" y las pendientes antes de activarlas.

## Fuentes publicadas

| Fuente | Licencia / términos | Condiciones que aplicamos | Atribución que mostramos |
|---|---|---|---|
| EPC — Registers of Participants (SCT, SCT Inst, SDD Core, SDD B2B) | Términos en la página de registros | Se permite ver, descargar y poner a disposición. **No explotar comercialmente el registro como tal salvo como parte de una oferta más amplia** (nuestro caso: herramienta gratuita combinada con otras fuentes). Citar al EPC, indicar cambios, no sugerir respaldo. | "Fuente: European Payments Council (EPC), Register of Participants. Datos normalizados por Cryptopocket." |
| Banco de España — Lista IFM de España | Términos de uso de estadísticas + aviso legal | Uso libre; citar la fuente y la fecha de actualización; reproducción fiel; si se vendiera, avisar de que es gratuita. | "Fuente: Elaboración propia a partir de datos de la web del Banco de España (www.bde.es)." + fecha |
| Deutsche Bundesbank — Bankleitzahlendatei | Condiciones generales de uso del sitio | Guardar, reenviar y reproducir sin cambiar ni distorsionar la información, citando "Source: Deutsche Bundesbank". Publicación en internet "no vinculante". Uso comercial del texto/datos no regulado expresamente → **revisión recomendada**. | "Source: Deutsche Bundesbank (Bankleitzahlendatei)." |
| OeNB — SEPA-Verzeichnis | CC BY 4.0 (Impressum und Haftung, 2.2) | Uso comercial permitido con atribución y mención de la licencia. | "Quelle: Oesterreichische Nationalbank (OeNB), CC BY 4.0." |
| ČNB — Kódy bank | Condiciones de uso del sitio | Guardar, transmitir y reproducir citando "Zdroj: ČNB" sin alterar los hechos. | "Zdroj: ČNB." |
| BCE — Lista MFI | Disclaimer & Copyright | Uso libre citando al BCE; indicar modificaciones. Solo se usa para contrastar. | "Source: European Central Bank, List of MFIs." |
| GLEIF/SWIFT — BIC-to-LEI relationship | BIC/LEI Mapping Table License Agreement | Gratuita, mundial, transferible, cualquier fin incluido el comercial. Toda copia debe incluir el aviso de SWIFT. | "SWIFT © and database rights [fecha]. All rights reserved. www.swift.com/bic" |
| GLEIF — registros LEI | CC0 | Sin condiciones; se cita por buena práctica. | "LEI data: GLEIF, CC0." |
| SWIFT IBAN Registry (vía schwifty) | Descarga gratuita; sin términos de reproducción publicados | Se usan hechos técnicos (longitudes, posiciones), no el documento. | "IBAN structures: SWIFT IBAN Registry (ISO 13616), via schwifty (MIT)." |
| schwifty (código) | MIT | La licencia MIT cubre el código, **no** los datos de terceros que incluye. | — |

## Publicadas por decisión de Cryptopocket (riesgo aceptado, 29-10-2026)

NBB (BE), SIX Bank Master (CH, LI), Finanssiala (FI), HNB (HR), MNB (HU), Lietuvos bankas (LT), Bits (NO), NBP (PL), Bankinfrastruktur (SE), Banka Slovenije (SI), NBS (SK).

Son directorios oficiales de descarga pública sin una licencia de reutilización explícita (`license: UNKNOWN`). Vicente Romero de Ávila (COO) aprobó su publicación asumiendo el riesgo; consta en `DATA_SOURCES_REGISTRY.yaml` (`risk_accepted`). Se publican con la cita de cada organismo. El código solo admite esta excepción para `UNKNOWN`, nunca para `RESTRICTED` ni `EXCLUDED`. Recomendación: pedir confirmación escrita a cada organismo y retirar la fuente (`publish: false`) si alguno lo solicita.

Siguen sin publicar como directorio: Latvijas Banka (fichero de 2020) y Betaalvereniging (NL); esos países se identifican por prefijo BIC.

## Excluidas

| Fuente | Motivo |
|---|---|
| Datos de España incluidos en schwifty | Proceden de iban.es (web privada), no del Banco de España. |
| Datos de Italia incluidos en schwifty | BIC y códigos obtenidos de ibancalculator.com (servicio comercial). |
| Datos de Rumanía incluidos en schwifty | Web de terceros. |
| Ficheros `manual_*` de schwifty | Mantenidos a mano sin procedencia por registro. |
| Banque de France — FIB | Distribución bajo contrato de pago. |
| Pay.UK EISCD (sort codes) | Servicio de pago. |
| SwiftRef | Comercial; fuera de alcance por decisión de Cryptopocket. |

## Reglas

1. Que un fichero sea descargable gratis no implica que pueda republicarse.
2. No se usan canales con registro (Bundesbank ExtraNet/NExt, SIX con credenciales) ni se eluden bloqueos o CAPTCHA.
3. Los datos se normalizan (formato, espacios, códigos) sin alterar los hechos; la web lo indica ("Datos normalizados por Cryptopocket").
4. La página `/tools/{es|en}/fuentes-y-licencias/` muestra todas las atribuciones y fechas.
