// Pruebas del motor JS contra resultados de schwifty (tests/fixtures/iban_cases.json)
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const SepaEngine = require('../../web/engine/sepa-engine.js');

const fx = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'fixtures', 'iban_cases.json'), 'utf8'));
const specs = {};
for (const [p, s] of Object.entries(fx.specs)) specs[p] = { ...s, name: { en: p, es: p }, directory: 'none' };
const engine = SepaEngine.create({ fetchJSON: (u) => u.endsWith('iban-specs.json') ? Promise.resolve(specs) : Promise.reject(new Error('n/a')) });

test('validación IBAN coincide con schwifty en todos los casos', async () => {
  const fails = [];
  const byKind = {};
  for (const c of fx.cases) {
    const v = await engine.validateIban(c.iban);
    byKind[c.kind] = (byKind[c.kind] || 0) + 1;
    if (v.iban_valid !== c.expect_valid) fails.push({ c, got: v });
    if (c.expect_valid && c.bank !== undefined && c.bank !== '') {
      const e = await engine.extractBankCode(c.iban);
      if (e.national_bank_code !== c.bank) fails.push({ c, got: e, what: 'bank' });
      if (c.branch && e.branch_code !== c.branch) fails.push({ c, got: e, what: 'branch' });
    }
  }
  if (fails.length) console.log(JSON.stringify(fails.slice(0, 10), null, 1));
  console.log('casos por tipo', byKind, 'total', fx.cases.length);
  assert.strictEqual(fails.length, 0, `${fails.length} discrepancias`);
});

test('los 42 prefijos (41 países SEPA + Gibraltar) tienen especificación', () => {
  assert.strictEqual(Object.keys(specs).length, 42);
});

test('normalización: espacios, guiones, minúsculas y prefijo IBAN', () => {
  assert.strictEqual(engine.normalizeIban(' iban es91-2100.0418 4502 0005 1332 '), 'ES9121000418450200051332');
});

test('entradas maliciosas o enormes no rompen el motor', async () => {
  for (const x of ['<script>alert(1)</script>', 'A'.repeat(10000), null, undefined, 12345, '¿?']) {
    const v = await engine.validateIban(x);
    assert.strictEqual(v.iban_valid, false);
  }
});
