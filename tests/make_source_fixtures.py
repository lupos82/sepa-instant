"""Ficheros de prueba SINTÉTICOS en el formato real de cada fuente.

Las entidades son ficticias ("ENTIDAD DE PRUEBA ...") y los BIC usan prefijos que no
pretenden representar bancos reales. Sirven para probar parsers, fusión y sincronización.
"""
import csv
import gzip
import io
import os
import zipfile


def epc_csv(rows):
    out = io.StringIO()
    w = csv.writer(out, quoting=csv.QUOTE_ALL)
    w.writerow(["Country", "ParticipantName", "Address", "City", "BIC", "Readiness Date", "Scheme Leaving Date", "Scheme Options"])
    for r in rows:
        w.writerow(r)
    return out.getvalue().encode("utf-8")


def bundesbank_txt(rows):
    widths = [8, 1, 58, 5, 35, 27, 5, 11, 2, 6, 1, 1, 8]
    lines = []
    for r in rows:
        lines.append("".join(str(v).ljust(n)[:n] for v, n in zip(r, widths)))
    return ("\r\n".join(lines) + "\r\n").encode("latin-1")


def oenb_csv(rows):
    hdr = ("Kennzeichen;Identnummer;Bankleitzahl;Institutsart;Sektor;Firmenbuchnummer;Bankenname;Straße;PLZ;Ort;"
           "Postadresse / Straße;Postadresse / PLZ;Postadresse / Ort;Postfach;Bundesland;Telefon;Fax;E-Mail;SWIFT-Code;Homepage;Gründungsdatum;LEI")
    lines = ["Die Oesterreichische Nationalbank aktualisiert die Daten täglich.", "Nutzung nur unter Haftungsausschluss.",
             "", "SEPA-Verzeichnis-Abfrage vom 28.10.2026", "", hdr]
    for r in rows:
        k, code, art, name, ort, bic, lei = r
        lines.append(f"{k};1;{code};{art};x;;{name};Str 1;1010;{ort};;;;;W;;;;{bic};;01.01.2000;{lei}")
    return ("\n".join(lines) + "\n").encode("cp1252")


def cnb_csv(rows):
    lines = ["Kód banky;Název;SWIFT"] + [f"{c};{n};{b}" for c, n, b in rows]
    return ("\n".join(lines) + "\n").encode("utf-8")


def bde_csv(rows):
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")
    w.writerow(["Código europeo", "LEI", "Nombre", "Categoría", "Dirección", "Informe", "Entidad matriz", "Código supervisor"])
    for r in rows:
        w.writerow(r)
    return out.getvalue().encode("utf-8")


def ecb_csv(rows):
    hdr = ["RIAD_CODE", "LEI", "COUNTRY_OF_REGISTRATION", "NAME", "BOX", "ADDRESS", "POSTAL", "CITY", "CATEGORY",
           "HEAD_COUNTRY_OF_REGISTRATION", "HEAD_NAME", "HEAD_RIAD_CODE", "HEAD_LEI", "REPORT"]
    text = "\t".join(hdr) + "\n" + "\n".join("\t".join(r) for r in rows) + "\n"
    return gzip.compress(text.encode("utf-16"))


def gleif_zip(rows):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["BIC", "LEI"])
    for r in rows:
        w.writerow(r)
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("BIC-LEI-20260901.csv", out.getvalue())
    return b.getvalue()


LEI_A = "TESTLEI0000000000001"[:18] + "01"
LEI_B = "TESTLEI0000000000002"[:18] + "02"
LEI_C = "TESTLEI0000000000003"[:18] + "03"


def base_set():
    epc_rows = [
        ["SPAIN", "ENTIDAD DE PRUEBA UNO, S.A.", "Calle 1", "MADRID", "TSTAESM1XXX", "2017-11-21", "", ""],
        ["SPAIN", "ENTIDAD DE PRUEBA DOS, S.A.", "Calle 2", "BILBAO", "TSTBESB1XXX", "2018-01-10", "", ""],
        ["GERMANY", "Prüfbank Eins AG", "Str 1", "Berlin", "TSTCDEB1XXX", "2019-05-01", "", ""],
        ["AUSTRIA", "Testbank Österreich AG", "Str 2", "Wien", "TSTDATW1XXX", "2020-02-02", "", ""],
        ["NETHERLANDS", "Proefbank N.V.", "Weg 1", "Amsterdam", "TSTENL21XXX", "2018-06-01", "", ""],
        ["UNITED KINGDOM", "Testing Bank plc", "Road 1", "London", "TSTFGB21XXX", "2019-09-09", "", ""],
        ["UNITED KINGDOM", "Other Testing Ltd", "Road 2", "Leeds", "TSTFGB22XXX", "2020-01-01", "", ""],
        ["FRANCE", "Banque Test SA", "Rue 1", "Paris", "TSTGFRPPXXX", "2030-01-01", "", ""],
        ["FRANCE", "Banque Partie SA", "Rue 2", "Lyon", "TSTHFRPPXXX", "2015-01-01", "2020-01-01", ""],
        ["SPAIN", "ENTIDAD DE PRUEBA UNO, S.A.", "Calle 1", "MADRID", "TSTAESM1XXX", "2017-11-21", "", ""],  # duplicado
    ]
    sct = epc_rows + [[f"GERMANY", f"Prüfbank Nr {i}", "Str", "Köln", f"TSX{chr(65 + i % 26)}DEK{i % 10}XXX", "2010-01-01", "", ""] for i in range(10)]
    bb = [
        ["10010099", "1", "Prüfbank Eins AG", "10115", "Berlin", "Prüfbank Eins", "", "TSTCDEB1XXX", "00", "000001", "U", "0", "00000000"],
        ["10010099", "2", "Prüfbank Eins AG", "10117", "Berlin-Mitte", "Prüfbank Eins", "", "", "00", "000002", "U", "0", "00000000"],
        ["20020099", "1", "Prüfbank Zwei eG", "20095", "Hamburg", "Prüfbank Zwei", "", "TSTIDEH1XXX", "09", "000003", "U", "1", "10010099"],
        ["30030099", "1", "Prüfbank Drei", "40210", "Düsseldorf", "Prüfbank Drei", "", "", "00", "000004", "A", "0", "00000000"],
    ]
    oenb = [["Hauptanstalt", "99901", "KI", "Testbank Österreich AG", "Wien", "TSTDATW1XXX", LEI_C],
            ["Zweigstelle", "99901", "", "Testbank Österreich AG Filiale", "Graz", "", ""],
            ["Hauptanstalt", "99902", "KI", "Zweite Testbank AG", "Linz", "TSTJATW2XXX", ""]]
    cnb = [["9901", "Testovací banka a.s.", "TSTKCZPP"], ["9902", "Druhá testovací banka", ""]]
    bde = [["ES9901", LEI_A, "ENTIDAD DE PRUEBA UNO, S.A.", "Entidad de crédito", "Calle 1, Madrid", "Sí", "", "9901"],
           ["ES9902", LEI_B, "ENTIDAD DE PRUEBA DOS, S.A.", "Entidad de crédito", "Calle 2, Bilbao", "Sí", "", "9902"],
           ["ES9903", "", "ENTIDAD DE PRUEBA TRES, S.A.", "Entidad de crédito", "Calle 3", "No", "", "9903"],
           ["ESX0000001", "", "FONDO MONETARIO DE PRUEBA", "Fondos del mercado monetario", "", "Sí", "", ""],
           ["ES9000", "", "BANCO DE ESPAÑA", "Banco central", "Alcalá 48", "Sí", "", "9000"]]
    ecb = [["ES9901", LEI_A, "ES", "ENTIDAD DE PRUEBA UNO, S.A.", "", "", "", "MADRID", "Credit institution", "", "", "", "", "Yes"],
           ["DE0000001", "", "DE", "Fondsgesellschaft", "", "", "", "Frankfurt", "Money market fund", "", "", "", "", "No"]]
    gleif = [["TSTAESM1XXX", LEI_A], ["TSTBESB1XXX", LEI_B], ["TSTBESB1BIL", LEI_B], ["TSTFGB21XXX", "TESTLEI00000000000GB4"[:18] + "44"],
             ["ZZZZUS33XXX", "TESTLEI00000000000US5"[:18] + "55"]]
    return {"epc_sct_inst": epc_csv(epc_rows), "epc_sct": epc_csv(sct), "epc_sdd_core": epc_csv(epc_rows[:5]),
            "epc_sdd_b2b": epc_csv(epc_rows[:3]), "bundesbank_blz": bundesbank_txt(bb), "oenb_sepa_directory": oenb_csv(oenb),
            "cnb_bank_codes": cnb_csv(cnb), "bde_mfi_es": bde_csv(bde), "ecb_mfi": ecb_csv(ecb), "gleif_bic_lei": gleif_zip(gleif)}


EXT = {"bundesbank_blz": "txt", "ecb_mfi": "csv.gz", "gleif_bic_lei": "zip"}


def write_set(dirpath, files):
    os.makedirs(dirpath, exist_ok=True)
    for sid, data in files.items():
        with open(os.path.join(dirpath, f"{sid}.{EXT.get(sid, 'csv')}"), "wb") as f:
            f.write(data)
