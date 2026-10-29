# -*- coding: utf-8 -*-
"""Textos, países y guías del sitio de herramientas (ES / EN)."""

# --------------------------------------------------------------------------
# Países: nombre EPC (inglés, mayúsculas) -> ISO, nombres y slugs por idioma
# --------------------------------------------------------------------------
COUNTRIES = {
    # epc name: (iso, en, es)
    "ALBANIA": ("AL", "Albania", "Albania"),
    "ANDORRA": ("AD", "Andorra", "Andorra"),
    "AUSTRIA": ("AT", "Austria", "Austria"),
    "BELGIUM": ("BE", "Belgium", "Bélgica"),
    "BULGARIA": ("BG", "Bulgaria", "Bulgaria"),
    "CROATIA": ("HR", "Croatia", "Croacia"),
    "CYPRUS": ("CY", "Cyprus", "Chipre"),
    "CZECH REPUBLIC": ("CZ", "Czech Republic", "República Checa"),
    "CZECHIA": ("CZ", "Czech Republic", "República Checa"),
    "DENMARK": ("DK", "Denmark", "Dinamarca"),
    "ESTONIA": ("EE", "Estonia", "Estonia"),
    "FINLAND": ("FI", "Finland", "Finlandia"),
    "FRANCE": ("FR", "France", "Francia"),
    "GERMANY": ("DE", "Germany", "Alemania"),
    "GIBRALTAR": ("GI", "Gibraltar", "Gibraltar"),
    "GREECE": ("GR", "Greece", "Grecia"),
    "GUERNSEY": ("GG", "Guernsey", "Guernsey"),
    "HUNGARY": ("HU", "Hungary", "Hungría"),
    "ICELAND": ("IS", "Iceland", "Islandia"),
    "IRELAND": ("IE", "Ireland", "Irlanda"),
    "ISLE OF MAN": ("IM", "Isle of Man", "Isla de Man"),
    "ITALY": ("IT", "Italy", "Italia"),
    "JERSEY": ("JE", "Jersey", "Jersey"),
    "LATVIA": ("LV", "Latvia", "Letonia"),
    "LIECHTENSTEIN": ("LI", "Liechtenstein", "Liechtenstein"),
    "LITHUANIA": ("LT", "Lithuania", "Lituania"),
    "LUXEMBOURG": ("LU", "Luxembourg", "Luxemburgo"),
    "MALTA": ("MT", "Malta", "Malta"),
    "MOLDOVA": ("MD", "Moldova", "Moldavia"),
    "MONACO": ("MC", "Monaco", "Mónaco"),
    "MONTENEGRO": ("ME", "Montenegro", "Montenegro"),
    "NETHERLANDS": ("NL", "Netherlands", "Países Bajos"),
    "NORTH MACEDONIA": ("MK", "North Macedonia", "Macedonia del Norte"),
    "NORWAY": ("NO", "Norway", "Noruega"),
    "POLAND": ("PL", "Poland", "Polonia"),
    "PORTUGAL": ("PT", "Portugal", "Portugal"),
    "ROMANIA": ("RO", "Romania", "Rumanía"),
    "SAN MARINO": ("SM", "San Marino", "San Marino"),
    "SERBIA": ("RS", "Serbia", "Serbia"),
    "SLOVAKIA": ("SK", "Slovakia", "Eslovaquia"),
    "SLOVENIA": ("SI", "Slovenia", "Eslovenia"),
    "SPAIN": ("ES", "Spain", "España"),
    "SWEDEN": ("SE", "Sweden", "Suecia"),
    "SWITZERLAND": ("CH", "Switzerland", "Suiza"),
    "UNITED KINGDOM": ("GB", "United Kingdom", "Reino Unido"),
    "VATICAN CITY STATE": ("VA", "Vatican City", "Ciudad del Vaticano"),
    "HOLY SEE": ("VA", "Vatican City", "Ciudad del Vaticano"),
}

# Nombres por ISO (para páginas de IBAN de países sin participantes)
ISO_NAMES = {iso: (en, es) for (iso, en, es) in COUNTRIES.values()}

# Países con IBAN SEPA para los que se genera página propia de validación
IBAN_COUNTRY_PAGES = [
    "AD", "AL", "AT", "BE", "BG", "CH", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR",
    "GB", "GI", "GR", "HR", "HU", "IE", "IS", "IT", "LI", "LT", "LU", "LV", "MC", "MD",
    "ME", "MK", "MT", "NL", "NO", "PL", "PT", "RO", "RS", "SE", "SI", "SK", "SM", "VA",
]

EUROZONE = {"AT", "BE", "BG", "HR", "CY", "EE", "FI", "FR", "DE", "GR", "IE", "IT",
            "LV", "LT", "LU", "MT", "NL", "PT", "SK", "SI", "ES"}
EU_NON_EURO = {"CZ", "DK", "HU", "PL", "RO", "SE"}


def regulation_text(iso, name, lang):
    """Párrafo sobre la obligación regulatoria según el país."""
    if iso == "BG":
        return {
            "es": f"{name} adoptó el euro el 1 de enero de 2026. Sus proveedores de pagos tienen hasta el 1 de enero de 2027 para cumplir las obligaciones de transferencias inmediatas, igualdad de comisiones y verificación del beneficiario del Reglamento (UE) 2024/886.",
            "en": f"{name} adopted the euro on 1 January 2026. Its payment service providers have until 1 January 2027 to meet the instant transfer, equal charges and Verification of Payee obligations of Regulation (EU) 2024/886.",
        }[lang]
    if iso in EUROZONE:
        return {
            "es": f"{name} pertenece a la zona euro. Por el Reglamento (UE) 2024/886, sus bancos deben poder recibir transferencias inmediatas en euros desde el 9 de enero de 2025 y enviarlas desde el 9 de octubre de 2025. Las entidades de pago y de dinero electrónico tienen hasta el 9 de abril de 2027.",
            "en": f"{name} is in the euro area. Under Regulation (EU) 2024/886, its banks must be able to receive instant euro transfers since 9 January 2025 and send them since 9 October 2025. Payment and e-money institutions have until 9 April 2027.",
        }[lang]
    if iso in EU_NON_EURO:
        return {
            "es": f"{name} es Estado miembro de la UE fuera de la zona euro. Sus proveedores de pagos que ofrecen cuentas en euros deben recibir transferencias inmediatas desde el 9 de enero de 2027 y enviarlas desde el 9 de julio de 2027.",
            "en": f"{name} is an EU member state outside the euro area. Its payment service providers that offer euro accounts must receive instant transfers from 9 January 2027 and send them from 9 July 2027.",
        }[lang]
    return {
        "es": f"{name} no es Estado miembro de la UE, así que los plazos del Reglamento (UE) 2024/886 no se le aplican de forma directa. Cada banco decide si se adhiere al esquema SEPA Instant.",
        "en": f"{name} is not an EU member state, so the deadlines of Regulation (EU) 2024/886 do not apply to it directly. Each bank decides whether to join the SEPA Instant scheme.",
    }[lang]


# --------------------------------------------------------------------------
# Rutas (slugs) por idioma
# --------------------------------------------------------------------------
SLUGS = {
    "en": {"sepa": "sepa-instant", "bank": "bank", "iban": "iban-checker", "bic": "bic-lookup", "guides": "guides",
           "identify": "iban-bank-lookup", "code": "bank-code-lookup", "sources": "sources-and-licences"},
    "es": {"sepa": "sepa-instant", "bank": "banco", "iban": "validar-iban", "bic": "buscar-bic", "guides": "guias",
           "identify": "identificar-banco-iban", "code": "codigo-banco", "sources": "fuentes-y-licencias"},
}

# --------------------------------------------------------------------------
# Textos de interfaz
# --------------------------------------------------------------------------
T = {
    "es": {
        "locale": "es-ES",
        "brand_tag": "Herramientas de pagos",
        "nav_sepa": "SEPA Instant", "nav_iban": "Validar IBAN", "nav_bic": "Buscar BIC", "nav_guides": "Guías",
        "contact": "Contactar",
        "other_lang": "English",
        "home": "Herramientas",
        "updated": "Datos actualizados el",
        "source_epc": "Fuente: registro oficial de participantes SCT Inst del European Payments Council (EPC), comprobado cada día.",
        "source_banks": "Códigos bancarios: directorios oficiales con licencia de reutilización verificada; estructuras IBAN del registro de SWIFT (ISO 13616) vía la librería abierta schwifty.",
        "disclaimer": "Información orientativa, sin garantía. Confirma los pagos críticos con tu proveedor de pagos.",
        "cta_h": "Pagos internacionales sin esperas",
        "cta_p": "Cryptopocket ofrece a empresas infraestructura regulada de pagos en euros y stablecoins: pagos transfronterizos rápidos, IBAN virtuales y on/off-ramp.",
        "cta_btn": "Habla con nuestro equipo",
        "yes": "Acepta SEPA Instant", "soon": "Se incorpora próximamente", "no": "No figura en SEPA Instant",
        "since": "Adherido desde", "from": "A partir del",
        "bic": "BIC", "city": "Ciudad", "country": "País", "name": "Entidad", "status": "Estado",
        "scheme": "Esquema", "checked": "Última comprobación",
        "search_ph": "BIC, IBAN o nombre del banco",
        "faq": "Preguntas frecuentes",
        "related_inst": "Otros BIC de esta entidad",
        "related_city": "Otros bancos con SEPA Instant en",
        "related_country": "Más bancos con SEPA Instant en",
        "all_countries": "Todos los países",
        "see_all": "Ver todos",
        "banks_n": "bancos",
        "participants": "Participantes", "countries": "Países", "latest": "Última adhesión",
        "guides_title": "Guías sobre pagos SEPA",
        "privacy_note": "La validación se hace en tu navegador: el IBAN no se envía a ningún servidor ni se guarda.",
        "tool_loading": "Cargando…",
        "nav_identify": "Banco por IBAN", "nav_code": "Código bancario",
        "source_line": "Fuentes: Banco de España, Deutsche Bundesbank, OeNB, ČNB, BCE, EPC y GLEIF/SWIFT (ver detalle de fuentes y licencias).",
        "sources_link": "Fuentes y licencias",
    },
    "en": {
        "locale": "en-GB",
        "brand_tag": "Payment tools",
        "nav_sepa": "SEPA Instant", "nav_iban": "IBAN checker", "nav_bic": "BIC lookup", "nav_guides": "Guides",
        "contact": "Contact",
        "other_lang": "Español",
        "home": "Tools",
        "updated": "Data updated on",
        "source_epc": "Source: official SCT Inst register of participants of the European Payments Council (EPC), checked daily.",
        "source_banks": "Bank codes: official directories with verified reuse terms; IBAN structures from the SWIFT IBAN Registry (ISO 13616) via the open-source schwifty library.",
        "disclaimer": "For guidance only, without warranty. Confirm critical payments with your payment provider.",
        "cta_h": "Cross-border payments without the wait",
        "cta_p": "Cryptopocket gives businesses regulated euro and stablecoin payment infrastructure: fast cross-border payments, virtual IBANs and on/off-ramp.",
        "cta_btn": "Talk to our team",
        "yes": "Accepts SEPA Instant", "soon": "Joining soon", "no": "Not listed in SEPA Instant",
        "since": "Participant since", "from": "From",
        "bic": "BIC", "city": "City", "country": "Country", "name": "Institution", "status": "Status",
        "scheme": "Scheme", "checked": "Last checked",
        "search_ph": "BIC, IBAN or bank name",
        "faq": "Frequently asked questions",
        "related_inst": "Other BICs of this institution",
        "related_city": "Other SEPA Instant banks in",
        "related_country": "More SEPA Instant banks in",
        "all_countries": "All countries",
        "see_all": "See all",
        "banks_n": "banks",
        "participants": "Participants", "countries": "Countries", "latest": "Latest joiner",
        "guides_title": "Guides to SEPA payments",
        "privacy_note": "Validation runs in your browser: the IBAN is never sent to a server or stored.",
        "tool_loading": "Loading…",
        "nav_identify": "Bank by IBAN", "nav_code": "Bank code",
        "source_line": "Sources: Banco de España, Deutsche Bundesbank, OeNB, ČNB, ECB, EPC and GLEIF/SWIFT (see sources and licences).",
        "sources_link": "Sources and licences",
    },
}

# --------------------------------------------------------------------------
# Guías (HTML sencillo). Datos verificados con el BCE, el EPC y el
# Reglamento (UE) 2024/886. Revisar si cambia la normativa.
# --------------------------------------------------------------------------
GUIDES = [
    {
        "key": "what",
        "slug": {"es": "que-es-sepa-instant", "en": "what-is-sepa-instant"},
        "title": {"es": "Qué es SEPA Instant y cómo funciona", "en": "What is SEPA Instant and how does it work"},
        "desc": {"es": "SEPA Instant (SCT Inst) permite enviar euros entre bancos europeos en menos de 10 segundos, a cualquier hora. Cómo funciona, límites y cobertura.",
                 "en": "SEPA Instant (SCT Inst) moves euros between European banks in under 10 seconds, at any time. How it works, limits and coverage."},
        "body": {
            "es": """
<p>SEPA Instant Credit Transfer (SCT Inst) es el esquema europeo de transferencias inmediatas en euros. Lo gestiona el European Payments Council (EPC) y funciona desde noviembre de 2017. El dinero llega a la cuenta del beneficiario en segundos, también por la noche, en fin de semana y en festivos.</p>
<h2>Cómo funciona</h2>
<ul>
<li><strong>Velocidad:</strong> el Reglamento (UE) 2024/886 fija un máximo de 10 segundos desde que el banco del ordenante recibe la orden hasta que el beneficiario tiene los fondos.</li>
<li><strong>Disponibilidad:</strong> 24 horas al día, 7 días a la semana, todos los días del año.</li>
<li><strong>Moneda:</strong> solo euros, entre cuentas de países SEPA.</li>
<li><strong>Confirmación:</strong> el ordenante sabe al momento si el pago se ha abonado o se ha rechazado.</li>
</ul>
<h2>¿Hay importe máximo?</h2>
<p>Desde el reglamento del esquema de octubre de 2025, SEPA Instant ya no tiene un importe máximo por operación. Antes era de 100.000 €. Cada banco puede fijar sus propios límites, y el Reglamento (UE) 2024/886 obliga a dejar que el cliente establezca un límite para sus pagos inmediatos.</p>
<h2>¿Qué bancos participan?</h2>
<p>Para recibir y enviar pagos SEPA Instant, la entidad debe estar adherida al esquema, directamente o a través de otra entidad. El EPC publica la lista oficial de participantes, que hoy reúne más de {participants} entidades en {countries} países. Puedes consultarla en nuestro <a href="{sepa_url}">buscador de SEPA Instant</a>.</p>
<h2>¿Cuánto cuesta?</h2>
<p>En la UE, un pago inmediato no puede costar más que una transferencia SEPA normal del mismo banco. En la zona euro rige desde el 9 de enero de 2025.</p>
""",
            "en": """
<p>SEPA Instant Credit Transfer (SCT Inst) is the European scheme for instant euro transfers. It is run by the European Payments Council (EPC) and has been live since November 2017. Funds reach the payee's account within seconds, including at night, at weekends and on public holidays.</p>
<h2>How it works</h2>
<ul>
<li><strong>Speed:</strong> Regulation (EU) 2024/886 sets a maximum of 10 seconds from the moment the payer's bank receives the order until the payee has the funds.</li>
<li><strong>Availability:</strong> 24 hours a day, 7 days a week, every day of the year.</li>
<li><strong>Currency:</strong> euro only, between accounts in SEPA countries.</li>
<li><strong>Confirmation:</strong> the payer knows immediately whether the payment was credited or rejected.</li>
</ul>
<h2>Is there a maximum amount?</h2>
<p>Since the October 2025 scheme rulebook, SEPA Instant no longer has a maximum amount per transaction. It used to be €100,000. Each bank can set its own limits, and Regulation (EU) 2024/886 requires banks to let customers set a limit for their instant payments.</p>
<h2>Which banks take part?</h2>
<p>To send and receive SEPA Instant payments, an institution must participate in the scheme, either directly or through another institution. The EPC publishes the official list of participants, currently over {participants} institutions in {countries} countries. You can search it with our <a href="{sepa_url}">SEPA Instant checker</a>.</p>
<h2>How much does it cost?</h2>
<p>In the EU, an instant payment cannot cost more than a regular SEPA transfer from the same bank. In the euro area this has applied since 9 January 2025.</p>
""",
        },
    },
    {
        "key": "ipr",
        "slug": {"es": "reglamento-pagos-inmediatos", "en": "instant-payments-regulation"},
        "title": {"es": "Reglamento europeo de pagos inmediatos: plazos y obligaciones", "en": "EU Instant Payments Regulation: deadlines and obligations"},
        "desc": {"es": "Plazos del Reglamento (UE) 2024/886 para recibir y enviar pagos inmediatos, igualdad de comisiones y verificación del beneficiario.",
                 "en": "Deadlines of Regulation (EU) 2024/886 for receiving and sending instant payments, equal charges and Verification of Payee."},
        "body": {
            "es": """
<p>El Reglamento (UE) 2024/886 obliga a los proveedores de pagos de la UE que ofrecen transferencias en euros a ofrecer también transferencias inmediatas. Entró en vigor el 8 de abril de 2024 y se aplica por fases.</p>
<h2>Calendario</h2>
<div class="tbl"><table>
<thead><tr><th>Obligación</th><th>Zona euro</th><th>UE fuera de la zona euro</th></tr></thead>
<tbody>
<tr><td>Recibir pagos inmediatos</td><td>9 ene 2025</td><td>9 ene 2027</td></tr>
<tr><td>Comisiones no superiores a una transferencia normal</td><td>9 ene 2025</td><td>9 ene 2027</td></tr>
<tr><td>Enviar pagos inmediatos</td><td>9 oct 2025</td><td>9 jul 2027</td></tr>
<tr><td>Verificación del beneficiario</td><td>9 oct 2025</td><td>9 jul 2027</td></tr>
</tbody></table></div>
<p>Las entidades de pago y de dinero electrónico tienen plazos propios: recibir desde el 9 de abril de 2027 y enviar desde el 9 de abril de 2027 en la zona euro (9 de julio de 2027 fuera de ella). Bulgaria, que adoptó el euro en 2026, tiene hasta el 1 de enero de 2027.</p>
<h2>Qué cambia para empresas y particulares</h2>
<ul>
<li><strong>Pagos inmediatos en todos los bancos</strong> que ofrecen transferencias en euros, por los mismos canales: app, banca online o fichero.</li>
<li><strong>Sin sobrecoste:</strong> el pago inmediato no puede ser más caro que la transferencia normal.</li>
<li><strong>Verificación del beneficiario:</strong> antes de pagar, el banco comprueba que el nombre coincide con el IBAN. Ver la <a href="{vop_url}">guía de verificación del beneficiario</a>.</li>
<li><strong>Control de sanciones:</strong> los bancos revisan a sus clientes al menos una vez al día, en lugar de revisar cada pago.</li>
</ul>
<p>Para saber si un banco concreto ya participa en el esquema, usa el <a href="{sepa_url}">buscador de SEPA Instant</a>.</p>
""",
            "en": """
<p>Regulation (EU) 2024/886 requires EU payment service providers that offer euro credit transfers to also offer instant credit transfers. It entered into force on 8 April 2024 and applies in phases.</p>
<h2>Timeline</h2>
<div class="tbl"><table>
<thead><tr><th>Obligation</th><th>Euro area</th><th>EU outside the euro area</th></tr></thead>
<tbody>
<tr><td>Receive instant payments</td><td>9 Jan 2025</td><td>9 Jan 2027</td></tr>
<tr><td>Charges no higher than a regular transfer</td><td>9 Jan 2025</td><td>9 Jan 2027</td></tr>
<tr><td>Send instant payments</td><td>9 Oct 2025</td><td>9 Jul 2027</td></tr>
<tr><td>Verification of Payee</td><td>9 Oct 2025</td><td>9 Jul 2027</td></tr>
</tbody></table></div>
<p>Payment and e-money institutions have their own deadlines: receiving from 9 April 2027 and sending from 9 April 2027 in the euro area (9 July 2027 outside it). Bulgaria, which adopted the euro in 2026, has until 1 January 2027.</p>
<h2>What changes for businesses and consumers</h2>
<ul>
<li><strong>Instant payments at every bank</strong> that offers euro transfers, through the same channels: app, online banking or file upload.</li>
<li><strong>No extra cost:</strong> an instant payment cannot be more expensive than a regular transfer.</li>
<li><strong>Verification of Payee:</strong> before paying, the bank checks that the name matches the IBAN. See the <a href="{vop_url}">Verification of Payee guide</a>.</li>
<li><strong>Sanctions screening:</strong> banks check their customers at least once a day instead of screening each payment.</li>
</ul>
<p>To see whether a specific bank already participates in the scheme, use the <a href="{sepa_url}">SEPA Instant checker</a>.</p>
""",
        },
    },
    {
        "key": "vop",
        "slug": {"es": "verificacion-del-beneficiario", "en": "verification-of-payee"},
        "title": {"es": "Verificación del beneficiario (VoP): qué es y cómo funciona", "en": "Verification of Payee (VoP): what it is and how it works"},
        "desc": {"es": "Desde octubre de 2025, los bancos de la zona euro comprueban que el nombre del beneficiario coincide con el IBAN antes de cada transferencia.",
                 "en": "Since October 2025, euro area banks check that the payee's name matches the IBAN before every credit transfer."},
        "body": {
            "es": """
<p>La verificación del beneficiario, conocida como VoP (<em>Verification of Payee</em>), es un control que el banco hace antes de enviar una transferencia: compara el nombre que escribes con el titular real del IBAN. La exige el Reglamento (UE) 2024/886 para transferencias normales e inmediatas.</p>
<h2>Fechas</h2>
<ul>
<li><strong>Zona euro:</strong> desde el 9 de octubre de 2025.</li>
<li><strong>UE fuera de la zona euro:</strong> desde el 9 de julio de 2027.</li>
</ul>
<h2>Posibles resultados</h2>
<ul>
<li><strong>Coincide:</strong> el nombre y el IBAN corresponden al mismo titular.</li>
<li><strong>Coincidencia aproximada:</strong> el nombre es parecido. El banco te muestra el nombre correcto.</li>
<li><strong>No coincide:</strong> el banco te avisa de que el pago podría no llegar a quien crees.</li>
<li><strong>No se puede verificar:</strong> por ejemplo, si el banco del beneficiario no responde.</li>
</ul>
<p>Tú decides si continúas con el pago. Si sigues adelante tras un aviso de «no coincide», el banco puede no responder del error. El servicio es gratuito.</p>
<h2>Consejos para empresas</h2>
<ul>
<li>Guarda los nombres de los beneficiarios tal como figuran en su cuenta: razón social completa para empresas.</li>
<li>En pagos por fichero, revisa los avisos antes de autorizar el lote.</li>
<li>Valida el formato del IBAN antes de darlo de alta con nuestro <a href="{iban_url}">validador de IBAN</a>.</li>
</ul>
""",
            "en": """
<p>Verification of Payee (VoP) is a check the bank runs before sending a credit transfer: it compares the name you enter with the actual holder of the IBAN. Regulation (EU) 2024/886 requires it for both regular and instant transfers.</p>
<h2>Dates</h2>
<ul>
<li><strong>Euro area:</strong> since 9 October 2025.</li>
<li><strong>EU outside the euro area:</strong> from 9 July 2027.</li>
</ul>
<h2>Possible results</h2>
<ul>
<li><strong>Match:</strong> the name and the IBAN belong to the same holder.</li>
<li><strong>Close match:</strong> the name is similar. The bank shows you the correct name.</li>
<li><strong>No match:</strong> the bank warns you the payment may not reach the person you expect.</li>
<li><strong>Verification not possible:</strong> for example, when the payee's bank does not respond.</li>
</ul>
<p>You decide whether to proceed. If you go ahead after a "no match" warning, the bank may not be liable for the mistake. The service is free of charge.</p>
<h2>Tips for businesses</h2>
<ul>
<li>Store payee names exactly as they appear on the account: the full legal name for companies.</li>
<li>For bulk files, review the warnings before authorising the batch.</li>
<li>Check the IBAN format before adding a payee with our <a href="{iban_url}">IBAN checker</a>.</li>
</ul>
""",
        },
    },
    {
        "key": "vs",
        "slug": {"es": "sepa-instant-vs-sepa-estandar", "en": "sepa-instant-vs-sepa-credit-transfer"},
        "title": {"es": "SEPA Instant frente a SEPA estándar: diferencias", "en": "SEPA Instant vs standard SEPA transfer: differences"},
        "desc": {"es": "Plazo, horario, importes, coste y cobertura: en qué se diferencia una transferencia SEPA Instant de una transferencia SEPA normal.",
                 "en": "Speed, hours, amounts, cost and reach: how a SEPA Instant transfer differs from a regular SEPA credit transfer."},
        "body": {
            "es": """
<div class="tbl"><table>
<thead><tr><th></th><th>SEPA Instant (SCT Inst)</th><th>SEPA estándar (SCT)</th></tr></thead>
<tbody>
<tr><td>Plazo</td><td>Máximo 10 segundos</td><td>Hasta el siguiente día hábil</td></tr>
<tr><td>Horario</td><td>24/7, todos los días del año</td><td>Días hábiles bancarios</td></tr>
<tr><td>Importe máximo del esquema</td><td>Sin máximo desde octubre de 2025 (cada banco fija sus límites)</td><td>Sin máximo (cada banco fija sus límites)</td></tr>
<tr><td>Coste en la UE</td><td>No puede superar el de la transferencia normal</td><td>Según tarifa del banco</td></tr>
<tr><td>Confirmación</td><td>Inmediata: abonado o rechazado</td><td>Sin confirmación inmediata</td></tr>
<tr><td>Verificación del beneficiario</td><td>Sí</td><td>Sí</td></tr>
</tbody></table></div>
<h2>¿Cuándo usar cada una?</h2>
<p>SEPA Instant es útil cuando el plazo importa: pagos a proveedores con entrega inmediata, liquidaciones fuera de horario, devoluciones o nóminas urgentes. La transferencia normal sigue siendo válida para pagos programados sin urgencia.</p>
<h2>¿Qué pasa si el banco del beneficiario no participa?</h2>
<p>Si el banco de destino no está en el esquema, el pago inmediato se rechaza o, según tu banco, se envía como transferencia normal. Comprueba el banco antes de pagar con el <a href="{sepa_url}">buscador de SEPA Instant</a>.</p>
""",
            "en": """
<div class="tbl"><table>
<thead><tr><th></th><th>SEPA Instant (SCT Inst)</th><th>Standard SEPA (SCT)</th></tr></thead>
<tbody>
<tr><td>Speed</td><td>Maximum 10 seconds</td><td>Up to the next business day</td></tr>
<tr><td>Hours</td><td>24/7, every day of the year</td><td>Banking business days</td></tr>
<tr><td>Scheme maximum amount</td><td>No maximum since October 2025 (each bank sets its limits)</td><td>No maximum (each bank sets its limits)</td></tr>
<tr><td>Cost in the EU</td><td>Cannot exceed that of a regular transfer</td><td>Per the bank's price list</td></tr>
<tr><td>Confirmation</td><td>Immediate: credited or rejected</td><td>No immediate confirmation</td></tr>
<tr><td>Verification of Payee</td><td>Yes</td><td>Yes</td></tr>
</tbody></table></div>
<h2>When to use each</h2>
<p>SEPA Instant helps whenever timing matters: supplier payments with immediate delivery, out-of-hours settlements, refunds or urgent payroll. Regular transfers remain fine for scheduled payments with no urgency.</p>
<h2>What if the payee's bank does not participate?</h2>
<p>If the receiving bank is not in the scheme, the instant payment is rejected or, depending on your bank, sent as a regular transfer. Check the bank before paying with the <a href="{sepa_url}">SEPA Instant checker</a>.</p>
""",
        },
    },
    {
        "key": "check",
        "slug": {"es": "como-saber-si-un-banco-acepta-sepa-instant", "en": "how-to-check-if-a-bank-supports-sepa-instant"},
        "title": {"es": "Cómo saber si un banco acepta SEPA Instant", "en": "How to check if a bank supports SEPA Instant"},
        "desc": {"es": "Tres pasos para comprobar si el banco de un beneficiario puede recibir transferencias inmediatas, a partir del BIC o del IBAN.",
                 "en": "Three steps to check whether a payee's bank can receive instant transfers, starting from the BIC or the IBAN."},
        "body": {
            "es": """
<ol>
<li><strong>Consigue el BIC del banco.</strong> Aparece en las facturas o en los datos bancarios del beneficiario. Si solo tienes el IBAN, nuestro <a href="{identify_url}">identificador de banco por IBAN</a> extrae el código bancario y, en los países con directorio oficial disponible, muestra la entidad y su BIC.</li>
<li><strong>Búscalo en el registro del EPC.</strong> El <a href="{sepa_url}">buscador de SEPA Instant</a> consulta la lista oficial de participantes, actualizada cada día. Si el BIC exacto no figura, comprobamos también el de la oficina principal (terminado en XXX).</li>
<li><strong>Revisa la fecha.</strong> Algunas entidades aparecen con una fecha de incorporación futura: hasta ese día no aceptan pagos inmediatos.</li>
</ol>
<h2>Si el banco no aparece</h2>
<p>Que un banco no figure no siempre significa que no reciba pagos inmediatos: puede participar a través de otra entidad de su grupo o de un banco agente. En la zona euro, la regulación obliga a los bancos a recibir pagos inmediatos desde enero de 2025. Para pagos importantes, confirma con el banco del beneficiario o con tu proveedor.</p>
<h2>Para muchos beneficiarios a la vez</h2>
<p>Si pagas a muchos proveedores, <a href="{contact_url}">habla con nuestro equipo</a>: podemos ayudarte a automatizar la comprobación y el envío.</p>
""",
            "en": """
<ol>
<li><strong>Get the bank's BIC.</strong> It appears on invoices or in the payee's bank details. If you only have the IBAN, our <a href="{identify_url}">IBAN bank lookup</a> extracts the bank code and, in countries with an available official directory, shows the institution and its BIC.</li>
<li><strong>Look it up in the EPC register.</strong> The <a href="{sepa_url}">SEPA Instant checker</a> searches the official list of participants, updated daily. If the exact BIC is not listed, we also check the head office BIC (ending in XXX).</li>
<li><strong>Check the date.</strong> Some institutions are listed with a future joining date: until that day they do not accept instant payments.</li>
</ol>
<h2>If the bank is not listed</h2>
<p>A bank missing from the list may still receive instant payments through another institution in its group or an agent bank. In the euro area, regulation has required banks to receive instant payments since January 2025. For large payments, confirm with the payee's bank or your provider.</p>
<h2>For many payees at once</h2>
<p>If you pay many suppliers, <a href="{contact_url}">talk to our team</a>: we can help you automate checks and payouts.</p>
""",
        },
    },
    {
        "key": "identify",
        "slug": {"es": "como-saber-de-que-banco-es-un-iban", "en": "how-to-find-the-bank-of-an-iban"},
        "title": {"es": "Cómo saber de qué banco es un IBAN", "en": "How to find out which bank an IBAN belongs to"},
        "desc": {"es": "El IBAN contiene el código del banco. Dónde está en cada país, cómo se identifica la entidad y qué límites tiene la comprobación.",
                 "en": "The IBAN contains the bank's code. Where it sits in each country, how the institution is identified and what the check cannot tell you."},
        "body": {
            "es": """
<p>Cada IBAN incluye un código que identifica al banco. Su posición y longitud dependen del país: en España son los dígitos 5 a 8 (código de entidad del Banco de España), en Alemania los 8 dígitos del Bankleitzahl y en Francia los 5 dígitos del código banco.</p>
<h2>Ejemplos de estructura</h2>
<div class="tbl"><table>
<thead><tr><th>País</th><th>Longitud</th><th>Código bancario</th></tr></thead>
<tbody>
<tr><td>España</td><td>24</td><td>4 dígitos (posiciones 5–8)</td></tr>
<tr><td>Alemania</td><td>22</td><td>8 dígitos (posiciones 5–12)</td></tr>
<tr><td>Francia</td><td>27</td><td>5 dígitos (posiciones 5–9)</td></tr>
<tr><td>Italia</td><td>27</td><td>5 dígitos ABI (posiciones 6–10, tras el carácter de control CIN)</td></tr>
<tr><td>Países Bajos</td><td>18</td><td>4 letras (posiciones 5–8)</td></tr>
<tr><td>Bélgica</td><td>16</td><td>3 dígitos (posiciones 5–7)</td></tr>
</tbody></table></div>
<h2>Cómo lo identificamos</h2>
<ol>
<li>Validamos el formato del país, los dígitos de control del IBAN y, cuando existe, el control nacional.</li>
<li>Extraemos el código bancario según la estructura oficial del registro IBAN de SWIFT.</li>
<li>Lo buscamos en directorios oficiales cuya licencia permite reutilizarlos (por ejemplo, el Banco de España o el Bundesbank).</li>
<li>Indicamos el BIC solo cuando una fuente lo relaciona con ese código, y si es un dato confirmado o un candidato.</li>
</ol>
<p>Pruébalo con nuestro <a href="{identify_url}">identificador de banco por IBAN</a>.</p>
<h2>Lo que un IBAN no dice</h2>
<ul>
<li>Que la cuenta exista o esté abierta: solo el banco puede confirmarlo.</li>
<li>Quién es el titular: para eso sirve la <a href="{vop_url}">verificación del beneficiario</a>.</li>
<li>Que una transferencia inmediata vaya a llegar: la adhesión a SEPA Instant es un requisito, no una garantía de entrega.</li>
</ul>
""",
            "en": """
<p>Every IBAN includes a code that identifies the bank. Its position and length depend on the country: in Spain it is digits 5 to 8 (Banco de España entity code), in Germany the 8-digit Bankleitzahl and in France the 5-digit bank code.</p>
<h2>Structure examples</h2>
<div class="tbl"><table>
<thead><tr><th>Country</th><th>Length</th><th>Bank code</th></tr></thead>
<tbody>
<tr><td>Spain</td><td>24</td><td>4 digits (positions 5–8)</td></tr>
<tr><td>Germany</td><td>22</td><td>8 digits (positions 5–12)</td></tr>
<tr><td>France</td><td>27</td><td>5 digits (positions 5–9)</td></tr>
<tr><td>Italy</td><td>27</td><td>5-digit ABI (positions 6–10, after the CIN check character)</td></tr>
<tr><td>Netherlands</td><td>18</td><td>4 letters (positions 5–8)</td></tr>
<tr><td>Belgium</td><td>16</td><td>3 digits (positions 5–7)</td></tr>
</tbody></table></div>
<h2>How we identify it</h2>
<ol>
<li>We validate the country format, the IBAN check digits and, where one exists, the national check.</li>
<li>We extract the bank code using the official structure in the SWIFT IBAN Registry.</li>
<li>We look it up in official directories whose licence allows reuse (for example Banco de España or the Bundesbank).</li>
<li>We show the BIC only when a source links it to that code, and say whether it is confirmed or a candidate.</li>
</ol>
<p>Try it with our <a href="{identify_url}">IBAN bank lookup</a>.</p>
<h2>What an IBAN does not tell you</h2>
<ul>
<li>Whether the account exists or is open: only the bank can confirm that.</li>
<li>Who holds it: that is what <a href="{vop_url}">Verification of Payee</a> is for.</li>
<li>That an instant transfer will arrive: SEPA Instant participation is a prerequisite, not a delivery guarantee.</li>
</ul>
""",
        },
    },

]
