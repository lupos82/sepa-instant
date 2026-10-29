// Pruebas de interfaz en navegador real (Playwright/Chromium) sobre el sitio generado con
// datos de prueba (tests/.tmp/site). Uso: node tests/e2e/site.e2e.js <dir_sitio> <dir_capturas>
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const SITE = path.resolve(process.argv[2] || 'tests/.tmp/site');
const SHOTS = path.resolve(process.argv[3] || 'tests/.tmp/shots');
fs.mkdirSync(SHOTS, { recursive: true });
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.xml': 'application/xml' };
const requests = [];
const CSP = (fs.readFileSync(path.join(__dirname, '..', '..', 'integration', 'tools.htaccess'), 'utf8').match(/Content-Security-Policy "([^"]+)"/) || [])[1] || '';
const server = http.createServer((req, res) => {
  requests.push(req.url);
  let p = decodeURIComponent(req.url.split('?')[0]);
  let f = path.join(SITE, p);
  if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
  if (!fs.existsSync(f)) { res.writeHead(404); return res.end('404'); }
  // Misma Content-Security-Policy que integration/tools.htaccess: cualquier violación aparece como error de consola.
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream', 'Content-Security-Policy': CSP });
  fs.createReadStream(f).pipe(res);
});

function iban(cc, bban) {
  let num = ''; for (const ch of bban + cc + '00') num += parseInt(ch, 36).toString();
  let r = 0; for (let i = 0; i < num.length; i += 7) r = parseInt(String(r) + num.substr(i, 7), 10) % 97;
  return cc + String(98 - r).padStart(2, '0') + bban;
}
function esBban(bank, branch, account) {
  const w = [1, 2, 4, 8, 5, 10, 9, 7, 3, 6], rec = (n) => n === 11 ? 0 : n === 10 ? 1 : n;
  const ws = (v, x) => { let s = 0; for (let i = 0; i < v.length; i++) s += x[i] * +v[i]; return s % 11; };
  return bank + branch + rec(11 - ws(bank + branch, w.slice(2))) + rec(11 - ws(account, w)) + account;
}

const results = [];
async function check(name, fn) {
  try { await fn(); results.push({ name, ok: true }); console.log('ok   ', name); }
  catch (e) {
    const msg = String(e).slice(0, 300);
    results.push({ name, ok: false, error: msg });
    console.log('FAIL ', name, msg);
    if (process.env.GITHUB_ACTIONS) console.log(`::error title=e2e: ${name.replace(/[:,\n]/g, ' ')}::${msg.replace(/[\r\n]+/g, ' ')}`);
  }
}
function assert(c, m) { if (!c) throw new Error(m); }

process.on('unhandledRejection', (e) => {
  console.log('FAIL  error no controlado', String(e).slice(0, 300));
  if (process.env.GITHUB_ACTIONS) console.log('::error title=e2e::' + String(e).slice(0, 300).replace(/[\r\n]+/g, ' '));
  process.exit(1);
});
(async () => {
  await new Promise((r) => server.listen(0, r));
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch();
  const errors = [];
  const desk = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await desk.newPage();
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error' && !/fonts\.g|ERR_TUNNEL|net::ERR/.test(m.text())) errors.push(m.text()); });

  async function type(url, sel, value) {
    await page.goto(base + url, { waitUntil: 'domcontentloaded' });
    await page.fill(sel, value);
    await page.press(sel, 'Enter');
    await page.waitForFunction((s) => { const o = document.querySelector(s).closest('[data-tool]').querySelector('.out'); return o && o.innerText && !o.getAttribute('aria-busy'); }, sel, { timeout: 8000 });
    return page.locator(sel).locator('xpath=ancestor::section[1]').locator('.out').innerText();
  }

  const ES_OK = iban('ES', esBban('9901', '0001', '0123456789'));
  await check('ES: identificar banco por IBAN (4 secciones)', async () => {
    const t = await type('/tools/es/identificar-banco-iban/', '#q-identify', ES_OK.replace(/(.{4})/g, '$1 '));
    assert(/IBAN válido/.test(t) && /ENTIDAD DE PRUEBA UNO/.test(t) && /TSTAESM1XXX/.test(t) && /candidato/i.test(t), t);
    assert(/1 · IBAN/i.test(t) && /2 · Banco/i.test(t) && /3 · SEPA/i.test(t) && /4 · Información/i.test(t), 'faltan secciones');
    await page.screenshot({ path: path.join(SHOTS, 'es-identify.png'), fullPage: true });
  });
  await check('EN: IBAN lookup with invalid checksum', async () => {
    const bad = ES_OK.slice(0, 2) + (ES_OK[2] === '1' ? '2' : '1') + ES_OK.slice(3);
    const t = await type('/tools/en/iban-bank-lookup/', '#q-identify', bad);
    assert(/Invalid IBAN/.test(t), t);
  });
  await check('FR: sin directorio, se muestra el código extraído', async () => {
    const t = await type('/tools/es/identificar-banco-iban/', '#q-identify', 'FR1420041010050500013M02606');
    assert(/Directorio bancario no disponible/.test(t) && /20041/.test(t), t);
  });
  await check('BE: pendiente de licencia', async () => {
    const t = await type('/tools/es/validar-iban/', '#q-iban', 'BE68539007547034');
    assert(/pendiente de verificación de licencia/.test(t), t);
  });
  await check('Código bancario: selector de país + código (DE)', async () => {
    await page.goto(base + '/tools/es/codigo-banco/', { waitUntil: 'domcontentloaded' });
    await page.selectOption('#c-code', 'DE');
    await page.fill('#q-code', '10010099');
    await page.press('#q-code', 'Enter');
    await page.waitForFunction(() => /Prüfbank/.test(document.querySelector('[data-tool=code] .out').innerText), null, { timeout: 8000 });
    const t = await page.locator('[data-tool=code] .out').innerText();
    assert(/TSTCDEB1XXX/.test(t) && /confirmado/.test(t), t);
    await page.screenshot({ path: path.join(SHOTS, 'es-code.png'), fullPage: false });
  });
  await check('BIC: participación futura', async () => {
    const t = await type('/tools/es/buscar-bic/', '#q-bic', 'TSTGFRPPXXX');
    assert(/Adhesión futura/.test(t), t);
  });
  await check('SEPA: búsqueda por nombre con tildes', async () => {
    const t = await type('/tools/es/sepa-instant/', '#q-sepa', 'prufbank');
    assert(/Prüfbank/.test(t), t);
  });
  await check('Privacidad: el IBAN no viaja en ninguna petición', async () => {
    const leaked = requests.filter((u) => u.includes(ES_OK) || u.includes(ES_OK.slice(4, 14)));
    assert(leaked.length === 0, 'IBAN en URL: ' + leaked.join(','));
  });
  await check('Privacidad: ?q= con IBAN se ignora', async () => {
    await page.goto(base + '/tools/es/sepa-instant/?q=' + ES_OK, { waitUntil: 'networkidle' });
    const v = await page.inputValue('#q-sepa');
    assert(v === '', 'se rellenó con el IBAN');
  });
  await check('Privacidad: la URL no cambia tras consultar un IBAN', async () => {
    const before = base + '/tools/es/validar-iban/';
    await type('/tools/es/validar-iban/', '#q-iban', ES_OK);
    assert(page.url() === before, 'URL cambió: ' + page.url());
    const stored = await page.evaluate(() => { const o = []; for (let i = 0; i < localStorage.length; i++) o.push(localStorage.getItem(localStorage.key(i))); for (let i = 0; i < sessionStorage.length; i++) o.push(sessionStorage.getItem(sessionStorage.key(i))); return o.join('|') + document.cookie; });
    assert(!stored.includes(ES_OK.slice(4, 14)), 'IBAN en almacenamiento del navegador');
  });
  await check('Entrada maliciosa: se muestra como texto, no se ejecuta', async () => {
    await page.goto(base + '/tools/es/sepa-instant/', { waitUntil: 'domcontentloaded' });
    await page.fill('#q-sepa', '<img src=x onerror="window.__xss=1">');
    await page.press('#q-sepa', 'Enter');
    await page.waitForTimeout(600);
    assert(!(await page.evaluate(() => window.__xss)), 'se ejecutó código');
    assert((await page.locator('[data-tool=sepa] .out img').count()) === 0, 'se insertó HTML');
  });
  await check('Teclado: tabulación llega al campo y Enter comprueba', async () => {
    await page.goto(base + '/tools/en/bic-lookup/', { waitUntil: 'domcontentloaded' });
    for (let i = 0; i < 25; i++) { await page.keyboard.press('Tab'); if (await page.evaluate(() => document.activeElement && document.activeElement.id === 'q-bic')) break; }
    assert(await page.evaluate(() => document.activeElement.id === 'q-bic'), 'el foco no llegó al campo');
    await page.keyboard.type('TSTAESM1');
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => /Registered/.test(document.querySelector('[data-tool=bic] .out').innerText), null, { timeout: 8000 });
  });
  await check('Página de código estático (SEO): contenido en el HTML sin JS', async () => {
    const html = fs.readFileSync(path.join(SITE, 'tools/es/codigo-banco/espana/9901/index.html'), 'utf8');
    assert(/<h1>Código de entidad \(NRBE, Banco de España\) 9901: ENTIDAD DE PRUEBA UNO, S\.A\.<\/h1>/.test(html), 'h1');
    assert(/rel="canonical" href="https:\/\/cryptopocket.io\/tools\/es\/codigo-banco\/espana\/9901\/"/.test(html), 'canonical');
    assert(/hreflang="en" href="https:\/\/cryptopocket.io\/tools\/en\/bank-code-lookup\/spain\/9901\/"/.test(html), 'hreflang');
  });

  const mob = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const mp = await mob.newPage();
  for (const u of ['/tools/es/', '/tools/es/identificar-banco-iban/', '/tools/en/bank-code-lookup/germany/', '/tools/es/codigo-banco/alemania/10010099/']) {
    await check('Móvil sin scroll horizontal: ' + u, async () => {
      await mp.goto(base + u, { waitUntil: 'domcontentloaded' });
      const w = await mp.evaluate(() => document.documentElement.scrollWidth);
      assert(w <= 391, 'scrollWidth=' + w);
    });
  }
  await mp.goto(base + '/tools/es/identificar-banco-iban/', { waitUntil: 'domcontentloaded' });
  await mp.fill('#q-identify', ES_OK); await mp.press('#q-identify', 'Enter');
  await mp.waitForTimeout(800);
  await mp.screenshot({ path: path.join(SHOTS, 'mobile-identify.png'), fullPage: true });
  const dark = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'dark' });
  const dp = await dark.newPage();
  await dp.goto(base + '/tools/en/iban-bank-lookup/', { waitUntil: 'domcontentloaded' });
  await dp.fill('#q-identify', 'BE68539007547034'); await dp.press('#q-identify', 'Enter'); await dp.waitForTimeout(700);
  await dp.screenshot({ path: path.join(SHOTS, 'dark-en.png') });

  await check('Raíz /tools/ redirige según idioma (sin JS en línea, con CSP)', async () => {
    await page.goto(base + '/tools/', { waitUntil: 'load' });
    await page.waitForURL(/\/tools\/(es|en)\/$/, { timeout: 5000 });
  });
  await check('Sin errores de JavaScript ni violaciones de CSP', async () => { assert(errors.length === 0, errors.join(' | ')); });
  await browser.close(); server.close();
  fs.writeFileSync(path.join(SHOTS, 'e2e-results.json'), JSON.stringify(results, null, 1));
  const failed = results.filter((r) => !r.ok).length;
  console.log(`\n${results.length - failed}/${results.length} pruebas de interfaz superadas`);
  process.exit(failed ? 1 : 0);
})();
