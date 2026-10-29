# Investigación de fuentes por país (41 países SEPA + Gibraltar)

Estado a 28-10-2026. "No localizada" significa que en esta investigación no se encontró una descarga pública oficial con términos verificables; no prueba que no exista. Las estructuras IBAN (posición y longitud del código) proceden del SWIFT IBAN Registry vía schwifty y se verifican con pruebas para los 42 prefijos.

| País | Organismo / fuente investigada | Descarga pública | Formato | Identificador en el IBAN | Relación con BIC | Actualización | Licencia | Estado en SEPA Tools |
|---|---|---|---|---|---|---|---|---|
| Alemania | Deutsche Bundesbank | Sí (web pública, no vinculante) | TXT/CSV/XML | BLZ 8 díg. (5–12) | BIC en el fichero | Trimestral | Atribución | **Publicado** (`bundesbank_blz`, respaldo `schwifty_de`) |
| Austria | OeNB | Sí | CSV | BLZ 5 díg. (5–9) | BIC y LEI en el fichero | Diaria | CC BY 4.0 | **Publicado** (`oenb_sepa_directory`) |
| España | Banco de España, lista IFM | Sí | CSV | Código de entidad 4 díg. (5–8) | Vía LEI → GLEIF (candidato) | Diaria | Atribución | **Publicado** (`bde_mfi_es`; sin EP/EDE) |
| República Checa | ČNB | Sí | CSV | 4 díg. (5–8) | BIC en el fichero | Con cambios | Atribución | **Publicado** (`cnb_bank_codes`) |
| Países Bajos | Betaalvereniging (lista BIC) | Sí | XLSX | 4 letras = BIC (5–8) | Directa | Con cambios | No verificada | **Publicado por prefijo BIC** (EPC+GLEIF); lista oficial pendiente |
| Reino Unido (+JE, GG, IM) | Pay.UK EISCD (sort codes) | No (de pago) | — | 4 letras = BIC + sort code | Prefijo BIC | — | Restringida | **Publicado por prefijo BIC** (EPC+GLEIF) |
| Irlanda | BPFI (NSC) | No localizada | — | 4 letras = BIC + NSC | Prefijo BIC | — | — | **Publicado por prefijo BIC** |
| Bulgaria | BNB | No localizada | — | 4 letras = BIC | Prefijo BIC | — | — | **Publicado por prefijo BIC** |
| Rumanía | BNR | No localizada | — | 4 letras = BIC | Prefijo BIC | — | — | **Publicado por prefijo BIC** (schwifty RO excluido) |
| Malta | CBM | No localizada | — | 4 letras = BIC + 5 díg. | Prefijo BIC | — | — | **Publicado por prefijo BIC** |
| Letonia | Latvijas Banka | Sí (fichero 2020) | XLS | 4 letras = BIC | Prefijo BIC | Desactualizado | No verificada | **Publicado por prefijo BIC**; lista oficial pendiente |
| Gibraltar | GFSC | No localizada | — | 4 letras = BIC | Prefijo BIC | — | — | **Publicado por prefijo BIC** |
| Bélgica | NBB (protocolo) | Sí | XLSX/XLS/PDF | 3 díg. (5–7) | BIC en la lista | Con cambios | No verificada ("fines exploratorios") | **Publicado (riesgo aceptado por Cryptopocket)** |
| Suiza | SIX Bank Master | Sí | JSON/CSV | IID 5 díg. (5–9) | BIC en el fichero | Diaria | No verificada | **Publicado (riesgo aceptado por Cryptopocket)** |
| Liechtenstein | SIX Bank Master | Sí | JSON/CSV | IID 5 díg. | BIC | Diaria | No verificada | **Publicado (riesgo aceptado por Cryptopocket)** |
| Finlandia | Finanssiala | Sí | XLSX | 3 díg. (5–7) | BIC | Con cambios | No verificada | **Publicado (riesgo aceptado por Cryptopocket)** |
| Croacia | HNB (VBB) | Sí | XLSX | 7 díg. (5–11) | BIC | Con cambios | No verificada | **Publicado (riesgo aceptado por Cryptopocket)** |
| Hungría | MNB | Sí | XLSX | 3 díg. (5–7) | BIC | Con cambios | No verificada | **Publicado (riesgo aceptado por Cryptopocket)** |
| Lituania | Lietuvos bankas | Sí | XML | 5 díg. (5–9) | BIC | Con cambios | No verificada | **Publicado (riesgo aceptado por Cryptopocket)** |
| Noruega | Bits AS | Sí | XLSX | 4 díg. (5–8) | BIC | Con cambios | No verificada | **Publicado (riesgo aceptado por Cryptopocket)** |
| Polonia | NBP (EWIB) | Sí | TXT | 8 díg. (5–12) | BIC | Diaria | No verificada | **Publicado (riesgo aceptado por Cryptopocket)** |
| Suecia | Bankinfrastruktur | Sí (PDF 2023) | PDF | 3 díg. (5–7) | BIC | Irregular | No verificada | **Publicado (riesgo aceptado por Cryptopocket)** |
| Eslovenia | Banka Slovenije | Sí | CSV | 2+3 díg. (5–9) | BIC | Con cambios | No verificada | **Publicado (riesgo aceptado por Cryptopocket)** |
| Eslovaquia | NBS | Sí | CSV | 4 díg. (5–8) | BIC | Con cambios | No verificada | **Publicado (riesgo aceptado por Cryptopocket)** |
| Francia | Banque de France (FIB) | No (contrato de pago) | — | 5 díg. (5–9) | — | — | Restringida | **Publicado vía lista MFI del BCE** (RIAD = FR+CIB) |
| Mónaco | Sistema francés (BdF) | No | — | 5 díg. | — | — | Restringida | **Publicado vía lista MFI del BCE** (bancos de Mónaco figuran con país FR) |
| Italia | Banca d'Italia (albo, GIAVA) | Solo consulta interactiva | — | ABI 5 díg. (6–10) | — | — | No verificada | Sin directorio (schwifty IT excluido) |
| San Marino | BCSM | No localizada | — | ABI 5 díg. (6–10) | — | — | — | Sin directorio |
| Portugal | Banco de Portugal ("Lista IBAN") | Referenciada, no localizada | — | 4 díg. (5–8) | — | — | — | Sin directorio (seguimiento recomendado) |
| Grecia | Bank of Greece (HEBIC) | No localizada | — | 3 díg. (5–7) | — | — | — | **Publicado vía lista MFI del BCE** (RIAD = GR+código, parcial) |
| Chipre | CBC | No localizada | — | 3 díg. (5–7) | — | — | — | Sin directorio |
| Luxemburgo | BCL / ABBL | No localizada | — | 3 díg. (5–7) | — | — | — | **Publicado vía lista MFI del BCE** (RIAD = LUB00+código) |
| Estonia | Eesti Pank | No localizada | — | 2 díg. (5–6) | — | — | — | Sin directorio |
| Dinamarca | Finans Danmark (reg. nr.) | No localizada | — | 4 díg. (5–8) | — | — | — | Sin directorio |
| Islandia | Seðlabanki | No localizada | — | 2 díg. (5–6) | — | — | — | Sin directorio |
| Andorra | INAF / AFA | No localizada | — | 4 díg. (5–8) | — | — | — | Sin directorio |
| Ciudad del Vaticano | ASIF | No localizada | — | 3 díg. (5–7) | — | — | — | Sin directorio |
| Albania | Banka e Shqipërisë | No localizada | — | 3 díg. (5–7) | — | — | — | Sin directorio |
| Moldavia | BNM | No localizada | — | 2 car. (5–6) | — | — | — | Sin directorio |
| Montenegro | CBCG | No localizada | — | 3 díg. (5–7) | — | — | — | Sin directorio |
| Macedonia del Norte | NBRNM | No localizada | — | 3 díg. (5–7) | — | — | — | Sin directorio |
| Serbia | NBS (Serbia) | No localizada | — | 3 díg. (5–7) | — | — | — | Sin directorio |

En todos los países, la búsqueda por BIC y la participación SEPA funcionan con los registros del EPC (BIC inscritos por país en `docs/SEPA_41_COUNTRIES_COVERAGE.md`).

## Siguientes pasos recomendados

1. Revisión legal de las 13 fuentes pendientes: una sola revisión activa 12 países.
2. Portugal: localizar la "Lista IBAN" del Banco de Portugal citada en su documentación.
3. Italia: consultar a Banca d'Italia si existe una descarga del albo con códigos ABI reutilizable.
4. Escribir conectores directos para las fuentes pendientes cuando se verifique su licencia (hoy se usan las copias de schwifty solo internamente).
