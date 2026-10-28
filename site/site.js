/* SEPA Tools 2.0 — interfaz de las herramientas (usa SepaEngine, web/engine/sepa-engine.js).
   Privacidad: el IBAN se procesa en el navegador; no se envía, no se guarda y no se pone en la URL. */
(function () {
  'use strict';
  var cfgEl = document.getElementById('cfg');
  if (!cfgEl || !window.SepaEngine) return;
  var C = JSON.parse(cfgEl.textContent), S = C.s, L = C.lang;
  var engine = window.SepaEngine.create({ baseUrl: C.data });

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function fmtD(d) { if (!d) return '–'; var x = new Date(String(d).slice(0, 10) + 'T12:00:00Z'); return isNaN(x) ? d : x.toLocaleDateString(C.locale, { day: 'numeric', month: 'long', year: 'numeric' }); }
  function cname(n) { return n ? (n[L] || n.en) : ''; }
  function bankUrl(bic) { return C.bankBase + bic.toLowerCase() + '/'; }
  function codeUrl(cc, code) { var slug = C.codeSlugs[cc]; return slug ? C.codeBase + slug + '/' + encodeURIComponent(code.toLowerCase()) + '/' : ''; }
  function row(label, value, cls) { return value ? '<dt>' + esc(label) + '</dt><dd' + (cls ? ' class="' + cls + '"' : '') + '>' + value + '</dd>' : ''; }
  function pill(text, cls) { return '<span class="pill ' + (cls || '') + '">' + esc(text) + '</span>'; }
  function verdict(cls, ic, title, body) { return '<div class="verdict ' + cls + '"><div class="ic" aria-hidden="true">' + ic + '</div><div><h3>' + esc(title) + '</h3>' + (body || '') + '</div></div>'; }

  /* ---------- secciones del resultado combinado ---------- */
  function ibanSection(r) {
    if (!r.iban_structure_valid) {
      var e = (r.errors || [])[0] || 'FORMAT';
      return verdict('bad', '✕', S.iban_bad, '<p>' + esc((S.err[e] || S.err.FORMAT).replace('{n}', r.expected_length || '')) + '</p>');
    }
    var ok = r.iban_valid;
    var natTxt = { VALID: S.nat_valid, INVALID: S.nat_invalid, NOT_AVAILABLE: S.nat_na }[r.national_check];
    var body = '<dl class="facts">' + row('IBAN', esc(r.iban_formatted), 'iban-fmt') +
      row(S.country, esc(cname(r.country_name)) + ' · ' + esc(r.country_code)) +
      row(S.checksum, r.iban_checksum_valid ? pill(S.ok, 'yes') : pill(S.wrong, 'bad')) +
      row(S.national, esc(natTxt)) + '</dl>';
    return '<section class="res-sec"><h3 class="sec-h">1 · IBAN</h3>' +
      verdict(ok ? 'yes' : 'bad', ok ? '✓' : '✕', ok ? S.iban_ok : S.iban_bad, '<p>' + esc(ok ? S.iban_ok_p : (S.err[(r.errors || [])[0]] || S.err.CHECKSUM)) + '</p>') +
      '<div class="panel">' + body + '</div></section>';
  }

  function bankSection(r) {
    var st = r.bank_identification_status;
    var head = '<section class="res-sec"><h3 class="sec-h">2 · ' + esc(S.bank_h) + '</h3>';
    var codeLine = row(S.code_type, esc(r.national_bank_code_type ? (r.national_bank_code_type[L] || r.national_bank_code_type.en) : '')) +
      row(S.bank_code, esc(r.national_bank_code), 'mono') + row(S.branch_code, esc(r.branch_code), 'mono');
    if (st === 'IDENTIFIED' || st === 'IDENTIFIED_BY_BIC_PREFIX' || st === 'AMBIGUOUS') {
      var bic = '';
      if (r.bic_candidates.length) {
        bic = r.bic_candidates.map(function (b) { return '<span class="pill bic">' + esc(b) + '</span>'; }).join(' ') +
          ' ' + pill(r.bic_status === 'CONFIRMED' ? S.bic_confirmed : S.bic_candidate, r.bic_status === 'CONFIRMED' ? 'yes' : 'soon');
      } else bic = esc(S.bic_none);
      var link = codeUrl(r.country_code, r.national_bank_code);
      var title = st === 'AMBIGUOUS' ? S.bank_ambiguous : S.bank_identified;
      return head + verdict(st === 'AMBIGUOUS' ? 'soon' : 'yes', st === 'AMBIGUOUS' ? '?' : '✓', title,
        '<p class="bank-name">' + esc(r.bank_name) + '</p>' + (r.bank_legal_name && r.bank_legal_name !== r.bank_name ? '<p>' + esc(r.bank_legal_name) + '</p>' : '')) +
        '<div class="panel"><dl class="facts">' + codeLine + row(S.city, esc(r.bank_city)) + row('BIC / SWIFT', bic) +
        (r.bank_status === 'DELETION_SCHEDULED' ? row(S.status, pill(S.deletion, 'soon') + (r.successor_code ? ' → ' + esc(r.successor_code) : '')) : '') +
        row('LEI', esc(r.lei), 'mono') + '</dl>' + (link && st === 'IDENTIFIED' ? '<p class="hint"><a href="' + link + '">' + esc(S.more_code) + ' →</a></p>' : '') + '</div></section>';
    }
    var msg = { NOT_FOUND: [S.bank_not_found, S.bank_not_found_p], DIRECTORY_NOT_AVAILABLE: [S.dir_none, S.dir_none_p],
      DIRECTORY_PENDING_LICENCE: [S.dir_pending, S.dir_pending_p] }[st];
    if (!msg) return '';
    return head + verdict('no', '!', msg[0], '<p>' + esc(msg[1]) + '</p>') + '<div class="panel"><dl class="facts">' + codeLine + '</dl></div></section>';
  }

  function sepaSection(r) {
    if (!r.bic_candidates || !r.bic_candidates.length) {
      if (!r.national_bank_code) return '';
      return '<section class="res-sec"><h3 class="sec-h">3 · SEPA</h3><p class="hint">' + esc(S.sepa_no_bic) + '</p></section>';
    }
    var names = { sct_participation_status: 'SEPA Credit Transfer (SCT)', sct_inst_participation_status: 'SEPA Instant (SCT Inst)',
      sdd_core_participation_status: 'SEPA Direct Debit Core', sdd_b2b_participation_status: 'SEPA Direct Debit B2B' };
    var keys = { sct_participation_status: 'SCT', sct_inst_participation_status: 'SCT_INST', sdd_core_participation_status: 'SDD_CORE', sdd_b2b_participation_status: 'SDD_B2B' };
    var rows = Object.keys(names).map(function (k) {
      var v = r[k], d = r.sepa_dates && r.sepa_dates[keys[k]];
      var t = { REGISTERED: [S.reg, 'yes'], FUTURE: [S.future, 'soon'], LEFT: [S.left, 'bad'], NOT_REGISTERED: [S.notreg, ''], UNKNOWN: [S.unknown, ''] }[v] || [v, ''];
      var extra = d ? ' <span class="hint-inline">' + esc(v === 'FUTURE' ? S.from + ' ' + fmtD(d.readiness) : v === 'LEFT' ? S.left_on + ' ' + fmtD(d.leaving) : S.since + ' ' + fmtD(d.readiness)) + '</span>' : '';
      return row(names[k], pill(t[0], t[1]) + extra);
    }).join('');
    var inst = r.sct_inst_participation_status;
    var v = inst === 'REGISTERED' ? verdict('yes', '✓', S.inst_yes, '<p>' + esc(S.inst_yes_p) + '</p>') :
      inst === 'FUTURE' ? verdict('soon', '…', S.inst_future, '<p>' + esc(S.inst_future_p.replace('{d}', fmtD(r.sepa_dates.SCT_INST.readiness))) + '</p>') :
      verdict('no', '!', S.inst_no, '<p>' + esc(S.inst_no_p) + '</p>');
    var link = r.sepa_bic ? '<p class="hint"><a href="' + bankUrl(r.sepa_bic) + '">' + esc(r.sepa_participant_name || r.sepa_bic) + ' · ' + esc(r.sepa_bic) + ' →</a></p>' : '';
    return '<section class="res-sec"><h3 class="sec-h">3 · SEPA</h3>' + v + '<div class="panel"><dl class="facts">' + rows + '</dl>' + link + '</div></section>';
  }

  function infoSection(r) {
    var w = (r.warnings || []).map(function (k) { return S.warn[k] ? '<li>' + esc(S.warn[k]) + '</li>' : ''; }).join('');
    var att = r.bank_source && r.bank_source.attribution ? String(r.bank_source.attribution).replace(/^(Fuente|Source|Quelle|Zdroj):\s*/i, '') : '';
    var src = att ? '<p>' + esc(S.bank_src) + ': ' + esc(att) + (r.bank_source_date ? ' (' + esc(fmtD(r.bank_source_date)) + ')' : '') + '</p>' : '';
    var epc = r.epc_register_date ? '<p>' + esc(S.epc_src) + ' (' + esc(fmtD(r.epc_register_date)) + ').</p>' : '';
    var fr = r.data_freshness && r.data_freshness.checked ? '<p>' + esc(S.checked) + ': ' + esc(fmtD(r.data_freshness.checked)) + '.</p>' : '';
    return '<section class="res-sec info"><h3 class="sec-h">4 · ' + esc(S.info_h) + '</h3><div class="panel">' + (w ? '<ul class="warns">' + w + '</ul>' : '') + src + epc + fr + '</div></section>';
  }

  function lookupHtml(r, opts) {
    opts = opts || {};
    return (opts.noIban ? '' : ibanSection(r)) + bankSection(r) + sepaSection(r) + infoSection(r);
  }

  function bicHtml(r) {
    if (!r.bic_valid) return verdict('bad', '✕', S.bic_bad, '<p>' + esc(S.bic_bad_p) + '</p>');
    var ids = (r.national_identifiers || []).map(function (x) { var u = codeUrl(x.country_code, x.national_bank_code); return u ? '<a href="' + u + '">' + esc(x.country_code + ' ' + x.national_bank_code) + '</a>' : esc(x.country_code + ' ' + x.national_bank_code); }).join(', ');
    var body = '<dl class="facts">' + row('BIC', '<span class="pill bic">' + esc(r.bic) + '</span>') + row(S.bank, esc(r.bank_name || S.not_identified)) +
      row(S.bic_inst, esc(r.institution_code), 'mono') + row(S.country, esc(r.country_code) + (r.country_name ? ' · ' + esc(cname(r.country_name)) : '')) +
      row(S.bic_loc, esc(r.location_code) + (r.is_test_bic ? ' · ' + esc(S.bic_test) : ''), 'mono') +
      row(S.bic_branch, esc(r.branch_code) + (r.is_head_office ? ' · ' + esc(S.bic_head) : ''), 'mono') + row(S.nat_ids, ids) + '</dl>';
    var fake = { bic_candidates: [r.bic], national_bank_code: null, sepa_bic: r.sepa_bic, sepa_dates: r.sepa_dates, sepa_participant_name: r.sepa_participant_name,
      sct_participation_status: r.sct_participation_status, sct_inst_participation_status: r.sct_inst_participation_status,
      sdd_core_participation_status: r.sdd_core_participation_status, sdd_b2b_participation_status: r.sdd_b2b_participation_status };
    return verdict('yes', '✓', S.bic_ok, '<p>' + esc(S.bic_ok_p) + '</p>') + '<div class="panel">' + body + '</div>' + sepaSection(fake) +
      infoSection({ warnings: r.warnings, epc_register_date: r.epc_register_date, data_freshness: r.data_freshness });
  }

  function namesHtml(res) {
    if (!res.results.length) return verdict('no', '!', S.none, '<p>' + esc(S.none_p) + '</p>');
    return '<div class="count">' + esc(S.results.replace('{n}', res.results.length).replace('{t}', res.total)) + '</div><div class="results">' +
      res.results.map(function (x) {
        var href = x.kind === 'bic' ? bankUrl(x.ref) : codeUrl(x.ref.split(':')[0], x.ref.split(':')[1]);
        var tag = x.kind === 'bic' ? x.ref : x.ref.replace(':', ' ');
        var inner = '<span><span class="n">' + esc(x.name) + '</span><br><span class="c">' + esc(C.countryNames[x.country_code] || x.country_code) + '</span></span><span class="r">' + esc(tag) + '</span>';
        return href ? '<a class="res" href="' + href + '">' + inner + '</a>' : '<div class="res">' + inner + '</div>';
      }).join('') + '</div>';
  }

  /* ---------- enlazar herramientas ---------- */
  var IBAN_RE = /^[A-Z]{2}\d{2}[A-Z0-9]{8,}$/, BIC_RE = /^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$/;
  document.querySelectorAll('[data-tool]').forEach(function (box) {
    var kind = box.getAttribute('data-tool');
    var input = box.querySelector('input[type=text]'), out = box.querySelector('.out'), sel = box.querySelector('select');
    var form = box.querySelector('form');
    var seq = 0, timer = null;
    function show(p) {
      var my = ++seq;
      out.setAttribute('aria-busy', 'true');
      out.innerHTML = '<p class="hint loading">' + esc(S.loading) + '</p>';
      p.then(function (html) { if (my === seq) { out.innerHTML = html; out.removeAttribute('aria-busy'); } },
        function () { if (my === seq) { out.innerHTML = verdict('bad', '✕', S.err_load_h, '<p>' + esc(S.err_load) + '</p>'); out.removeAttribute('aria-busy'); } });
    }
    function run() {
      var q = (input.value || '').trim().slice(0, 80);
      var v = q.toUpperCase().replace(/[\s\-.]/g, '');
      if (kind === 'code') {
        if (!sel.value || !v) { out.innerHTML = ''; return; }
        return show(engine.identifyByCode(sel.value, v).then(function (r) {
          if ((r.errors || []).indexOf('CODE_FORMAT') > -1) return verdict('bad', '✕', S.code_bad, '<p>' + esc(S.code_bad_p.replace('{n}', r.expected_code_length || '')) + '</p>');
          return lookupHtml(r, { noIban: true });
        }));
      }
      if (q.length < 2) { out.innerHTML = ''; return; }
      if (kind === 'iban' || kind === 'identify' || (kind === 'sepa' && IBAN_RE.test(v) && v.length >= 15)) return show(engine.identifyByIban(q).then(function (r) { return lookupHtml(r); }));
      if (kind === 'bic' || (kind === 'sepa' && BIC_RE.test(v))) {
        return show(engine.lookupBic(q).then(function (r) {
          if (kind === 'sepa' && r.bank_identification_status === 'NOT_FOUND' && r.sct_inst_participation_status === 'NOT_REGISTERED') {
            return engine.searchByName(q).then(function (n) { return n.total ? namesHtml(n) : bicHtml(r); });
          }
          return bicHtml(r);
        }));
      }
      return show(engine.searchByName(q, { country: sel && sel.value ? sel.value : '' }).then(namesHtml));
    }
    if (form) form.addEventListener('submit', function (e) { e.preventDefault(); clearTimeout(timer); run(); });
    input.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(run, kind === 'sepa' || kind === 'name' ? 150 : 300); });
    if (sel) sel.addEventListener('change', function () {
      var o = sel.options[sel.selectedIndex];
      if (kind === 'code' && o) { input.setAttribute('maxlength', o.getAttribute('data-len') || '12'); input.setAttribute('placeholder', o.getAttribute('data-ph') || ''); var h = box.querySelector('.code-hint'); if (h) h.textContent = o.getAttribute('data-hint') || ''; }
      run();
    });
    var clear = box.querySelector('[data-clear]');
    if (clear) clear.addEventListener('click', function () { input.value = ''; out.innerHTML = ''; input.focus(); });
    // Prefill por URL solo para BIC o nombre; nunca IBAN (privacidad)
    var pre = new URLSearchParams(location.search).get('q');
    if (pre && !IBAN_RE.test(pre.toUpperCase().replace(/[\s\-.]/g, '')) && kind !== 'iban' && kind !== 'identify') { input.value = pre.slice(0, 40); run(); }
    if (sel && box.getAttribute('data-country')) { sel.value = box.getAttribute('data-country'); sel.dispatchEvent(new Event('change')); }
  });
})();
