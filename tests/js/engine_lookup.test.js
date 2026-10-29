// Pruebas de identificación sobre el conjunto de datos de prueba (tests/build_fixture_dataset.py)
// y generación de ejemplos reales de respuesta para docs/api_examples.json.
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const SepaEngine = require('../../web/engine/sepa-engine.js');

const ROOT = process.env.SEPA_FIXTURE_ROOT || path.join(__dirname, '..', '.tmp', 'root');
const DATA = path.join(ROOT, 'data', 'v2');
const NOW = new Date('2026-10-28T12:00:00Z');
const fetchJSON = (u) => new Promise((res, rej) => {
  const p = path.join(DATA, u.replace(/^\/data\/v2\//, ''));
  fs.readFile(p, 'utf8', (e, d) => e ? rej(Object.assign(new Error('404'), { status: 404 })) : res(JSON.parse(d)));
});
const engine = SepaEngine.create({ fetchJSON, now: () => NOW });
const examples = {};

function iban(cc, bban) {
  const raw = bban + cc + '00';
  let num = ''; for (const ch of raw) num += parseInt(ch, 36).toString();
  let r = 0; for (let i = 0; i < num.length; i += 7) r = parseInt(String(r) + num.substr(i, 7), 10) % 97;
  return cc + String(98 - r).padStart(2, '0') + bban;
}
function esBban(bank, branch, account) {
  const w = [1, 2, 4, 8, 5, 10, 9, 7, 3, 6];
  const rec = (n) => n === 11 ? 0 : n === 10 ? 1 : n;
  const wsum = (v, ws) => { let s = 0; for (let i = 0; i < v.length; i++) s += ws[i] * +v[i]; return s % 11; };
  const d1 = rec(11 - wsum(bank + branch, w.slice(2))), d2 = rec(11 - wsum(account, w));
  return bank + branch + d1 + d2 + account;
}

test('banco identificado por IBAN (ES, código con prefijo 99)', async () => {
  const r = await engine.identifyByIban(iban('ES', esBban('9901', '0001', '0123456789')));
  examples.identified = r;
  assert.strictEqual(r.iban_valid, true);
  assert.strictEqual(r.national_check, 'VALID');
  assert.strictEqual(r.national_bank_code, '9901');
  assert.strictEqual(r.branch_code, '0001');
  assert.strictEqual(r.bank_identification_status, 'IDENTIFIED');
  assert.strictEqual(r.bank_name, 'ENTIDAD DE PRUEBA UNO, S.A.');
  assert.deepStrictEqual(r.bic_candidates, ['TSTAESM1XXX']);
  assert.strictEqual(r.bic_status, 'CANDIDATES');
  assert.strictEqual(r.sct_inst_participation_status, 'REGISTERED');
  assert.ok(r.warnings.includes('REACHABILITY_NOT_GUARANTEED'));
  assert.ok(r.warnings.includes('BIC_CANDIDATE_NOT_CONFIRMED'));
  assert.ok(r.warnings.includes('IBAN_VALID_NOT_ACCOUNT_EXISTENCE'));
});

test('IBAN inválido: no se identifica banco', async () => {
  const good = iban('ES', esBban('9901', '0001', '0123456789'));
  const r = await engine.identifyByIban(good.slice(0, 2) + (good[2] === '9' ? '0' : '9') + good.slice(3));
  examples.invalid_iban = r;
  assert.strictEqual(r.iban_valid, false);
  assert.ok(r.errors.includes('CHECKSUM'));
});

test('país sin directorio (IT): IBAN válido, banco no identificable', async () => {
  const r = await engine.identifyByIban('IT60X0542811101000000123456');
  examples.country_without_directory = r;
  assert.strictEqual(r.iban_valid, true);
  assert.strictEqual(r.national_bank_code, '05428');
  assert.strictEqual(r.bank_identification_status, 'DIRECTORY_NOT_AVAILABLE');
  assert.strictEqual(r.bank_name, null);
});

test('Francia por la lista MFI del BCE: identificado con aviso de origen', async () => {
  const r = await engine.identifyByIban('FR1420041010050500013M02606');
  examples.identified_by_ecb_list = r;
  assert.strictEqual(r.bank_identification_status, 'IDENTIFIED');
  assert.strictEqual(r.bank_name, 'BANQUE DE PRUEBA FRANCE');
  assert.strictEqual(r.bank_source.relation, 'ECB_RIAD_CONVENTION');
  assert.ok(r.warnings.includes('ECB_RIAD_CONVENTION') && r.warnings.includes('DIRECTORY_PARTIAL'));
  const lu = await engine.identifyByCode('LU', '99');
  assert.strictEqual(lu.bank_name, 'BANQUE DE PRUEBA LUXEMBOURG');
  const gr = await engine.identifyByCode('GR', '099');
  assert.strictEqual(gr.bank_name, 'TRAPEZA DOKIMIS S.A.');
});

test('país con directorio pendiente de licencia (BE)', async () => {
  const r = await engine.identifyByIban('BE68539007547034');
  examples.directory_pending_licence = r;
  assert.strictEqual(r.bank_identification_status, 'DIRECTORY_PENDING_LICENCE');
});

test('banco no encontrado: no se convierte en banco inexistente', async () => {
  const r = await engine.identifyByIban(iban('ES', esBban('9909', '0001', '0123456789')));
  examples.bank_not_found = r;
  assert.strictEqual(r.iban_valid, true);
  assert.strictEqual(r.bank_identification_status, 'NOT_FOUND');
  assert.strictEqual(r.bank_name, null);
});

test('correspondencia ambigua por prefijo BIC (GB)', async () => {
  const r = await engine.identifyByIban(iban('GB', 'TSTF' + '123456' + '12345678'));
  examples.ambiguous = r;
  assert.strictEqual(r.bank_identification_status, 'AMBIGUOUS');
  assert.ok(r.bic_candidates.length >= 2);
});

test('código con baja programada y sucesor (DE)', async () => {
  const r = await engine.identifyByCode('DE', '20020099');
  examples.deletion_scheduled = r;
  assert.strictEqual(r.bank_status, 'DELETION_SCHEDULED');
  assert.strictEqual(r.successor_code, '10010099');
  assert.ok(r.warnings.includes('CODE_DELETION_SCHEDULED'));
});

test('búsqueda por código: rellena ceros y valida longitud', async () => {
  const r = await engine.identifyByCode('ES', '9901');
  assert.strictEqual(r.bank_name, 'ENTIDAD DE PRUEBA UNO, S.A.');
  const bad = await engine.identifyByCode('ES', '99011');
  assert.ok(bad.errors.includes('CODE_FORMAT'));
  const at = await engine.identifyByCode('AT', '99901');
  assert.deepStrictEqual(at.bic_candidates, ['TSTDATW1XXX']);
  assert.strictEqual(at.bic_status, 'CONFIRMED');
  const nl = await engine.identifyByCode('NL', 'tste');
  assert.strictEqual(nl.bank_name, 'Proefbank N.V.');
});

test('BIC: formato, oficina principal, SEPA y participación futura', async () => {
  const r = await engine.lookupBic('TSTAESM1');
  examples.bic_lookup = r;
  assert.strictEqual(r.bic, 'TSTAESM1XXX');
  assert.strictEqual(r.is_head_office, true);
  assert.strictEqual(r.sct_inst_participation_status, 'REGISTERED');
  const fut = await engine.lookupBic('TSTGFRPPXXX');
  assert.strictEqual(fut.sct_inst_participation_status, 'FUTURE');
  const left = await engine.lookupBic('TSTHFRPPXXX');
  assert.strictEqual(left.sct_inst_participation_status, 'LEFT');
  const none = await engine.lookupBic('QQQQESMMXXX');
  assert.strictEqual(none.bank_identification_status, 'NOT_FOUND');
  assert.strictEqual(none.sct_inst_participation_status, 'NOT_REGISTERED');
  const bad = await engine.lookupBic('12345');
  assert.strictEqual(bad.bic_valid, false);
  const branch = await engine.lookupBic('TSTBESB1BIL');
  assert.strictEqual(branch.sepa_match, 'HEAD_OFFICE');
});

test('búsqueda por nombre: tildes, mayúsculas, parcial y filtro de país', async () => {
  const r = await engine.searchByName('prufbank');
  assert.ok(r.results.some((x) => x.name.startsWith('Prüfbank')));
  const es = await engine.searchByName('entidad prueba', { country: 'ES' });
  assert.ok(es.results.length >= 2 && es.results.every((x) => x.country_code === 'ES'));
  const none = await engine.searchByName('x');
  assert.strictEqual(none.total, 0);
});

test('estado y cobertura', async () => {
  const st = await engine.getStatus();
  examples.status = st;
  assert.ok(st.data_version);
  const cov = await engine.getCoverage('ES');
  assert.strictEqual(cov.directory, 'published');
});

test('guardar ejemplos de respuesta', () => {
  if (process.env.SEPA_WRITE_EXAMPLES) fs.writeFileSync(process.env.SEPA_WRITE_EXAMPLES, JSON.stringify(examples, null, 1));
});

test('esquema sin datos descargados: estado UNKNOWN, nunca "no figura"', async () => {
  const fx = (u) => fetchJSON(u).then((d) => (u.endsWith('meta.json') ? { ...d, schemes_available: ['SCT_INST'] } : d));
  const e2 = SepaEngine.create({ fetchJSON: fx, now: () => NOW });
  const r = await e2.lookupBic('QQQQESMMXXX');
  assert.strictEqual(r.sct_participation_status, 'UNKNOWN');
  assert.strictEqual(r.sct_inst_participation_status, 'NOT_REGISTERED');
});
