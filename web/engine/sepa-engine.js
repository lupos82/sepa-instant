/*! SEPA Tools 2.0 — motor de identificación bancaria (Cryptopocket). Contrato: docs/API_CONTRACT.md
 *  Funciona en navegador y en Node (>=18). No envía el IBAN a ningún servidor: solo descarga
 *  ficheros estáticos de datos (iban-specs.json, banks/<PAÍS>.json, sepa.json...).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.SepaEngine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var ENGINE_VERSION = '2.0.0';
  var SCHEMES = ['SCT', 'SCT_INST', 'SDD_CORE', 'SDD_B2B'];
  var STALE_DAYS = 3;
  var MAX_INPUT = 64;

  /* ------------------------------------------------------------------ utilidades */
  function normalizeIban(input) {
    return String(input == null ? '' : input).slice(0, MAX_INPUT * 2).toUpperCase().replace(/[\s\-.]/g, '').replace(/^IBAN/, '');
  }
  function normalizeBic(input) {
    var b = String(input == null ? '' : input).slice(0, MAX_INPUT).toUpperCase().replace(/[\s\-.]/g, '');
    if (!/^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$/.test(b)) return '';
    return b.length === 8 ? b + 'XXX' : b;
  }
  function normName(s) {
    return String(s || '').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  }
  var ALNUM = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  function numerifyStr(s) { var o = ''; for (var i = 0; i < s.length; i++) o += String(ALNUM.indexOf(s[i])); return o; }
  function modBig(numStr, m) { var r = 0; for (var i = 0; i < numStr.length; i += 7) r = parseInt(String(r) + numStr.substr(i, 7), 10) % m; return r; }
  function mod97Iban(v) { return modBig(numerifyStr(v.slice(4) + v.slice(0, 4)), 97); }
  function weighted(value, mod, weights) {
    var s = 0, n = Math.min(value.length, weights.length);
    for (var i = 0; i < n; i++) s += weights[i] * parseInt(value[i], 10);
    return s % mod;
  }
  function pad2(n) { return (n < 10 ? '0' : '') + n; }
  function comp(bban, pos, k) { var p = pos[k]; return p ? bban.slice(p[0], p[1]) : ''; }

  /* ------------------------------------------------------------------ controles nacionales (equivalentes a schwifty) */
  var FR_MAP = { A: 1, B: 2, C: 3, D: 4, E: 5, F: 6, G: 7, H: 8, I: 9, J: 1, K: 2, L: 3, M: 4, N: 5, O: 6, P: 7, Q: 8, R: 9, S: 2, T: 3, U: 4, V: 5, W: 6, X: 7, Y: 8, Z: 9 };
  var IT_ODD = [1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23];
  function itIndex(c) { return /\d/.test(c) ? parseInt(c, 10) : c.charCodeAt(0) - 65; }
  function frNum(s) { var o = ''; for (var i = 0; i < s.length; i++) o += /\d/.test(s[i]) ? s[i] : String(FR_MAP[s[i]]); return o; }
  function luhn(value) {
    var num = numerifyStr(value), s = 0, rev = num.split('').reverse();
    for (var i = 0; i < rev.length; i++) { var d = (2 - i % 2) * parseInt(rev[i], 10); String(d).split('').forEach(function (x) { s += parseInt(x, 10); }); }
    return String((10 - s % 10) % 10);
  }
  function esReconcile(n) { return n === 11 ? 0 : n === 10 ? 1 : n; }

  var NATIONAL = {
    es_ccc: function (b, p) {
      var w = [1, 2, 4, 8, 5, 10, 9, 7, 3, 6];
      var d1 = esReconcile(11 - weighted(comp(b, p, 'bank') + comp(b, p, 'branch'), 11, w.slice(2)));
      var d2 = esReconcile(11 - weighted(comp(b, p, 'account'), 11, w));
      return String(d1) + String(d2);
    },
    be_mod97: function (b, p) {
      var r = modBig(numerifyStr(comp(b, p, 'bank') + comp(b, p, 'branch') + comp(b, p, 'account')), 97);
      return pad2(r !== 0 ? r : 97);
    },
    fr_rib: function (b, p) {
      // 89*banco + 15*oficina + 3*cuenta, módulo 97 (se calcula con aritmética modular)
      var bank = modBig(frNum(comp(b, p, 'bank')), 97), br = modBig(frNum(comp(b, p, 'branch')), 97), acc = modBig(frNum(comp(b, p, 'account')), 97);
      var r = (89 * bank + 15 * br + 3 * acc) % 97;
      return pad2(97 - r);
    },
    it_cin: function (b, p) {
      var v = comp(b, p, 'bank') + comp(b, p, 'branch') + comp(b, p, 'account'), s = 0;
      for (var i = 0; i < v.length; i++) s += ((i + 1) % 2 === 0) ? itIndex(v[i]) : IT_ODD[itIndex(v[i])];
      return String.fromCharCode(65 + s % 26);
    },
    fi_luhn: function (b, p) { return luhn(comp(b, p, 'bank') + comp(b, p, 'account')); },
    ee_731: function (b, p) {
      var v = (comp(b, p, 'branch') + comp(b, p, 'account')).split('').reverse(), w = [7, 3, 1], s = 0;
      for (var i = 0; i < v.length; i++) s += w[i % 3] * parseInt(v[i], 10);
      var d = s % 10; return String(d === 0 ? 0 : 10 - d);
    },
    pl_weighted: function (b, p) {
      var d = weighted(comp(b, p, 'bank') + comp(b, p, 'branch'), 10, [3, 9, 7, 1, 3, 9, 7]);
      return String(d === 0 ? 0 : 10 - d);
    },
    no_mod11: function (b, p) {
      var acc = comp(b, p, 'account'), v = acc.slice(0, 2) === '00' ? acc.slice(2) : comp(b, p, 'bank') + acc;
      var c = 11 - weighted(v, 11, [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]);
      if (c === 10) return null; // la cuenta no admite dígito de control válido
      return String(c % 11);
    },
    iso7064_97_10: function (b, p) {
      var r = modBig(numerifyStr(comp(b, p, 'bank') + comp(b, p, 'branch') + comp(b, p, 'account')) + '00', 97);
      return pad2(98 - r);
    }
  };

  function nationalCheck(spec, bban) {
    var alg = spec.national_check, pos = spec.positions;
    if (!alg || !NATIONAL[alg]) return 'NOT_AVAILABLE';
    var where = pos.check;
    if (!where) return 'NOT_AVAILABLE';
    var expected = bban.slice(where[0], where[1]);
    var got;
    try { got = NATIONAL[alg](bban, pos); } catch (e) { return 'INVALID'; }
    return got !== null && got === expected ? 'VALID' : 'INVALID';
  }

  /* ------------------------------------------------------------------ motor */
  function create(opts) {
    opts = opts || {};
    var base = opts.baseUrl || '/data/v2/';
    var fetchJSON = opts.fetchJSON || function (u) {
      return fetch(u, { credentials: 'omit' }).then(function (r) { if (!r.ok) { var e = new Error('HTTP ' + r.status); e.status = r.status; throw e; } return r.json(); });
    };
    var now = opts.now || function () { return new Date(); };
    var cache = {};
    function load(name) {
      if (!cache[name]) cache[name] = fetchJSON(base + name).catch(function (e) { delete cache[name]; throw e; });
      return cache[name];
    }
    function loadOptional(name) { return load(name).catch(function () { return null; }); }
    function specs() { return load('iban-specs.json'); }
    function meta() { return loadOptional('meta.json'); }

    function freshness() {
      return Promise.all([meta(), loadOptional('status.json')]).then(function (r) {
        var m = r[0] || {}, st = r[1] || {};
        var checked = st.checked || '';
        var stale = checked ? (now() - new Date(checked)) / 864e5 > STALE_DAYS : null;
        return { data_version: m.data_version || '', checked: checked, stale: stale };
      });
    }

    function validateIban(input) {
      var v = normalizeIban(input);
      return specs().then(function (S) {
        var out = { input_normalized: v, country_code: v.slice(0, 2), iban_structure_valid: false, iban_checksum_valid: false,
          iban_valid: false, national_check: 'NOT_AVAILABLE', errors: [] };
        if (v.length > MAX_INPUT) { out.errors.push('TOO_LONG'); return out; }
        if (!/^[A-Z]{2}[0-9]{2}[A-Z0-9]+$/.test(v)) { out.errors.push(v.length < 5 ? 'INCOMPLETE' : 'INVALID_CHARACTERS'); return out; }
        var sp = S[v.slice(0, 2)];
        if (!sp) { out.errors.push('UNSUPPORTED_COUNTRY'); return out; }
        out.country_name = sp.name;
        if (v.length < sp.length) { out.errors.push('INCOMPLETE'); out.expected_length = sp.length; return out; }
        if (v.length > sp.length) { out.errors.push('WRONG_LENGTH'); out.expected_length = sp.length; return out; }
        var bban = v.slice(4);
        if (!new RegExp(sp.bban_regex).test(bban)) { out.errors.push('WRONG_STRUCTURE'); return out; }
        out.iban_structure_valid = true;
        out.iban_checksum_valid = mod97Iban(v) === 1;
        if (!out.iban_checksum_valid) out.errors.push('CHECKSUM');
        out.national_check = nationalCheck(sp, bban);
        if (out.national_check === 'INVALID') out.errors.push('NATIONAL_CHECK');
        out.iban_valid = out.iban_checksum_valid && out.national_check !== 'INVALID';
        out.formatted = v.replace(/(.{4})/g, '$1 ').trim();
        return out;
      });
    }

    function extractBankCode(input) {
      var v = normalizeIban(input);
      return specs().then(function (S) {
        var sp = S[v.slice(0, 2)];
        if (!sp) return null;
        var bban = v.slice(4), pos = sp.positions;
        return { country_code: sp.prefix, national_bank_code: comp(bban, pos, 'bank') || null,
          branch_code: comp(bban, pos, 'branch') || null, national_bank_code_type: sp.code_type,
          lookup_key: comp(bban, pos, 'bank') + (sp.lookup_branch ? comp(bban, pos, 'branch') : '') };
      });
    }

    function sepaFor(bic) {
      if (!bic) return Promise.resolve(null);
      return load('sepa.json').then(function (P) {
        var b = normalizeBic(bic);
        if (P[b]) return { bic: b, match: 'EXACT', entry: P[b] };
        if (P[b.slice(0, 8) + 'XXX']) return { bic: b.slice(0, 8) + 'XXX', match: 'HEAD_OFFICE', entry: P[b.slice(0, 8) + 'XXX'] };
        return null;
      });
    }

    function sepaFields(res, hit, m, haveBic) {
      var srcs = (m && m.sources) || {};
      res.epc_register_date = (srcs.epc_sct_inst && srcs.epc_sct_inst.effective_date) || null;
      var avail = (m && m.schemes_available) || SCHEMES;
      SCHEMES.forEach(function (s) { res[s.toLowerCase() + '_participation_status'] = ((hit || haveBic) && avail.indexOf(s) > -1) ? 'NOT_REGISTERED' : 'UNKNOWN'; });
      res.sepa_bic = null; res.sepa_match = 'NONE'; res.sepa_dates = {};
      if (!hit) return res;
      res.sepa_bic = hit.bic; res.sepa_match = hit.match; res.sepa_participant_name = hit.entry.n;
      SCHEMES.forEach(function (s) {
        var x = hit.entry.s[s];
        if (x) {
          var on = now().toISOString().slice(0, 10), st = x[1] && x[1] <= on ? 'LEFT' : (x[0] && x[0] > on ? 'FUTURE' : 'REGISTERED');
          res[s.toLowerCase() + '_participation_status'] = st;
          res.sepa_dates[s] = { readiness: x[0] || null, leaving: x[1] || null };
        }
      });
      if (res.sct_inst_participation_status === 'REGISTERED') res.warnings.push('REACHABILITY_NOT_GUARANTEED');
      if (res.sct_inst_participation_status === 'FUTURE') res.warnings.push('FUTURE_PARTICIPATION');
      if (hit.match === 'HEAD_OFFICE') res.warnings.push('SEPA_MATCH_HEAD_OFFICE');
      return res;
    }

    function base0() {
      return { engine_version: ENGINE_VERSION, lookup_timestamp: now().toISOString(), country_code: null, country_name: null,
        iban_valid: null, iban_checksum_valid: null, iban_structure_valid: null, national_check: null,
        national_bank_code: null, national_bank_code_type: null, branch_code: null,
        bank_name: null, bank_legal_name: null, bank_city: null, lei: null, bank_status: null, successor_code: null,
        bic_candidates: [], bic_status: 'NONE', bic_relation: null,
        bank_identification_status: null, bank_source: null, bank_source_date: null,
        warnings: [], errors: [], data_freshness: null };
    }

    function resolveCode(res, prefix, key, sp, m) {
      if (sp.directory === 'none') { res.bank_identification_status = 'DIRECTORY_NOT_AVAILABLE'; return Promise.resolve(res); }
      if (sp.directory === 'pending_licence') { res.bank_identification_status = 'DIRECTORY_PENDING_LICENCE'; return Promise.resolve(res); }
      return load('banks/' + prefix + '.json').then(function (D) {
        var e = D.codes[key];
        if (!e && sp.lookup_branch) e = D.codes[res.national_bank_code];
        res.bank_source_date = D.effective_date || null;
        var src = (m && m.sources && m.sources[D.source]) || null;
        if (!e) {
          res.bank_identification_status = 'NOT_FOUND';
          if (D.relation === 'BIC_PREFIX_CONVENTION') res.warnings.push('DIRECTORY_PARTIAL');
          res.bank_source = { id: D.source, attribution: D.attribution, relation: D.relation };
          return res;
        }
        var esrc = (m && m.sources && m.sources[e.s]) || src || {};
        res.bank_name = e.n; res.bank_legal_name = e.ln || e.n; res.bank_city = e.c || null; res.lei = e.l || null;
        res.bank_status = e.st || 'ACTIVE'; res.successor_code = e.su || null;
        res.bic_candidates = e.b || []; res.bic_status = e.bs || 'NONE'; res.bic_relation = e.br || null;
        res.bank_identification_status = e.amb ? 'AMBIGUOUS' : (D.relation === 'BIC_PREFIX_CONVENTION' ? 'IDENTIFIED_BY_BIC_PREFIX' : 'IDENTIFIED');
        res.bank_source = { id: e.s, institution: esrc.institution || null, license: esrc.license || null,
          attribution: esrc.attribution || D.attribution || null, url: esrc.url || null, relation: D.relation };
        if (e.bs === 'CANDIDATES') res.warnings.push(e.br === 'BIC_PREFIX_CONVENTION' ? 'BIC_PREFIX_CONVENTION' : 'BIC_CANDIDATE_NOT_CONFIRMED');
        if (e.st === 'DELETION_SCHEDULED') res.warnings.push('CODE_DELETION_SCHEDULED');
        if (e.x) res.warnings.push('SOURCE_CONFLICT');
        if (D.source === 'bde_mfi_es') res.warnings.push('DIRECTORY_PARTIAL');
        if (/^schwifty_/.test(D.source)) res.warnings.push('FALLBACK_SOURCE');
        return res;
      }).catch(function () { res.bank_identification_status = 'DIRECTORY_NOT_AVAILABLE'; res.errors.push('DATA_LOAD'); return res; });
    }

    function finish(res, m) {
      var bic = res.bic_candidates && res.bic_candidates[0];
      return sepaFor(bic).then(function (hit) {
        sepaFields(res, hit, m, !!bic);
        return freshness();
      }).then(function (f) {
        res.data_freshness = f;
        if (f.stale) res.warnings.push('DATA_STALE');
        return res;
      });
    }

    function identifyByIban(input) {
      var res = base0();
      return Promise.all([validateIban(input), specs(), meta()]).then(function (r) {
        var v = r[0], S = r[1], m = r[2];
        res.country_code = v.country_code || null; res.country_name = v.country_name || null;
        res.iban_valid = v.iban_valid; res.iban_checksum_valid = v.iban_checksum_valid; res.iban_structure_valid = v.iban_structure_valid;
        res.national_check = v.national_check; res.errors = v.errors.slice(); res.iban_formatted = v.formatted || null;
        if (!v.iban_structure_valid) { res.bank_identification_status = 'NOT_APPLICABLE'; return finish(res, m); }
        var sp = S[v.country_code], bban = v.input_normalized.slice(4), pos = sp.positions;
        res.national_bank_code = comp(bban, pos, 'bank') || null; res.branch_code = comp(bban, pos, 'branch') || null;
        res.national_bank_code_type = sp.code_type;
        res.warnings.push('IBAN_VALID_NOT_ACCOUNT_EXISTENCE');
        if (v.national_check === 'NOT_AVAILABLE') res.warnings.push('NATIONAL_CHECK_NOT_AVAILABLE');
        if (!v.iban_checksum_valid) res.warnings.push('IDENTIFICATION_FROM_INVALID_IBAN');
        var key = res.national_bank_code + (sp.lookup_branch ? (res.branch_code || '') : '');
        return resolveCode(res, sp.prefix, key, sp, m).then(function () { return finish(res, m); });
      });
    }

    function identifyByCode(country, code) {
      var res = base0();
      var prefix = String(country || '').toUpperCase().slice(0, 2);
      var c = String(code || '').toUpperCase().replace(/[\s\-.]/g, '').slice(0, 16);
      return Promise.all([specs(), meta()]).then(function (r) {
        var S = r[0], m = r[1], sp = S[prefix];
        if (!sp) { res.errors.push('UNSUPPORTED_COUNTRY'); res.bank_identification_status = 'NOT_APPLICABLE'; return res; }
        res.country_code = prefix; res.country_name = sp.name; res.national_bank_code_type = sp.code_type;
        var bp = sp.positions.bank, len = bp ? bp[1] - bp[0] : 0;
        var br = sp.positions.branch, blen = br ? br[1] - br[0] : 0;
        var numeric = !sp.bic_prefix_rule && prefix !== 'MD';
        if (!bp) { res.errors.push('CODE_FORMAT'); res.bank_identification_status = 'NOT_APPLICABLE'; return res; }
        if (numeric && !/^\d+$/.test(c)) { res.errors.push('CODE_FORMAT'); res.expected_code_length = len; res.bank_identification_status = 'NOT_APPLICABLE'; return res; }
        if (numeric && c.length < len) c = ('0000000000' + c).slice(-len);
        var full = sp.lookup_branch ? len + blen : len;
        if (c.length !== len && c.length !== full) { res.errors.push('CODE_FORMAT'); res.expected_code_length = len; res.bank_identification_status = 'NOT_APPLICABLE'; return res; }
        res.national_bank_code = c.slice(0, len);
        if (c.length > len) res.branch_code = c.slice(len);
        return resolveCode(res, prefix, c, sp, m).then(function () { return finish(res, m); });
      });
    }

    function lookupBic(input) {
      var b = normalizeBic(input);
      var res = { engine_version: ENGINE_VERSION, lookup_timestamp: now().toISOString(), bic: b || null, bic_valid: !!b, warnings: [], errors: [] };
      if (!b) { res.errors.push('BIC_FORMAT'); return Promise.resolve(res); }
      res.institution_code = b.slice(0, 4); res.country_code = b.slice(4, 6); res.location_code = b.slice(6, 8); res.branch_code = b.slice(8);
      res.is_head_office = res.branch_code === 'XXX'; res.is_test_bic = b[7] === '0';
      return Promise.all([specs(), loadOptional('bic8.json'), meta()]).then(function (r) {
        var S = r[0], idx = r[1] || {}, m = r[2];
        var c = S[res.country_code];
        res.country_name = c ? c.name : null;
        var x = idx[b.slice(0, 8)];
        res.bank_name = x ? x.n : null;
        res.national_identifiers = x && x.k ? x.k.map(function (k) { var p = k.split(':'); return { country_code: p[0], national_bank_code: p[1] }; }) : [];
        res.bank_identification_status = x ? 'IDENTIFIED' : 'NOT_FOUND';
        if (res.is_test_bic) res.warnings.push('TEST_BIC');
        var tmp = { warnings: res.warnings };
        return sepaFor(b).then(function (hit) {
          sepaFields(tmp, hit, m, true);
          Object.keys(tmp).forEach(function (k) { if (k !== 'warnings') res[k] = tmp[k]; });
          if (!res.bank_name && hit) res.bank_name = hit.entry.n;
          return freshness();
        }).then(function (f) { res.data_freshness = f; return res; });
      });
    }

    function getSepaParticipation(bic) {
      var tmp = { warnings: [] };
      return Promise.all([sepaFor(bic), meta()]).then(function (r) { return sepaFields(tmp, r[0], r[1], !!normalizeBic(bic)); });
    }

    function searchByName(q, o) {
      o = o || {};
      var nq = normName(q).slice(0, 80), limit = Math.min(o.limit || 25, 100), cc = o.country ? String(o.country).toUpperCase() : '';
      if (nq.length < 2) return Promise.resolve({ query: nq, total: 0, results: [] });
      var terms = nq.split(' ');
      return load('names.json').then(function (N) {
        var hits = [];
        for (var i = 0; i < N.length; i++) {
          var r = N[i];
          if (cc && r[2] !== cc) continue;
          var ok = true;
          for (var t = 0; t < terms.length; t++) if (r[0].indexOf(terms[t]) === -1) { ok = false; break; }
          if (ok) hits.push({ name: r[1], country_code: r[2], kind: r[3], ref: r[4], starts: r[0].indexOf(nq) === 0 });
        }
        hits.sort(function (a, b) { return (b.starts - a.starts) || a.name.localeCompare(b.name); });
        return { query: nq, total: hits.length, results: hits.slice(0, limit) };
      });
    }

    function getStatus() {
      return Promise.all([meta(), loadOptional('status.json')]).then(function (r) {
        var m = r[0] || {}, st = r[1] || {};
        return { engine_version: ENGINE_VERSION, data_version: m.data_version || null, schwifty: m.schwifty || null,
          checked: st.checked || null, sources: m.sources || {}, source_status: st.sources || {}, conflicts: m.conflicts || 0 };
      });
    }
    function getCoverage(country) {
      return load('coverage.json').then(function (c) { return country ? (c.countries[String(country).toUpperCase()] || null) : c; });
    }
    function listCountries() {
      return specs().then(function (S) {
        return Object.keys(S).map(function (k) { var s = S[k]; return { prefix: k, iso: s.iso, name: s.name, directory: s.directory,
          code_type: s.code_type, bank_code_length: s.positions.bank ? s.positions.bank[1] - s.positions.bank[0] : 0,
          branch_code_length: s.positions.branch ? s.positions.branch[1] - s.positions.branch[0] : 0, lookup_branch: s.lookup_branch,
          bank_code_alpha: s.bic_prefix_rule }; });
      });
    }

    return { version: ENGINE_VERSION, normalizeIban: normalizeIban, normalizeBic: normalizeBic, validateIban: validateIban,
      extractBankCode: extractBankCode, identifyByIban: identifyByIban, identifyByCode: identifyByCode, lookupBic: lookupBic,
      searchByName: searchByName, getSepaParticipation: getSepaParticipation, getStatus: getStatus, getCoverage: getCoverage,
      listCountries: listCountries };
  }

  return { create: create, version: ENGINE_VERSION, _internal: { nationalCheck: nationalCheck, mod97Iban: mod97Iban, normalizeIban: normalizeIban } };
});
