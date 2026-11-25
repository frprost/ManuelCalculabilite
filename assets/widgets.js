/* widgets.js — simulateurs interactifs (machines de Turing, compilateur, castors, λ-calcul) */
(function () {
  'use strict';
  function el(tag, attrs, html) {
    var e = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { if (k === 'class') e.className = attrs[k]; else e.setAttribute(k, attrs[k]); });
    if (html !== undefined) e.innerHTML = html;
    return e;
  }
  function esc(s) { return String(s).replace(/[&<>]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]; }); }
  function parseArgs(s) {
    s = s.trim(); if (!s) return [];
    return s.split(/[,\s]+/).map(function (x) {
      var n = parseInt(x, 10); if (isNaN(n) || n < 0) throw new Error('Entrée invalide : « ' + x + ' » (entiers naturels séparés par des virgules)'); return n;
    });
  }
  function source(w) { var p = w.querySelector('pre.src, script[type="text/plain"]'); return p ? p.textContent.replace(/^\n/, '') : (w.dataset.prog || ''); }

  function dessinerBande(conteneur, c, largeur) {
    largeur = largeur || 12;
    var keys = Array.from(c.tape.keys());
    var lo = Math.min.apply(null, keys.concat([c.pos])) - 2, hi = Math.max.apply(null, keys.concat([c.pos])) + 2;
    if (hi - lo > 120) { lo = c.pos - 60; hi = c.pos + 60; }
    lo = Math.min(lo, c.pos - largeur / 2); hi = Math.max(hi, c.pos + largeur / 2);
    var h = '';
    for (var i = lo; i <= hi; i++) {
      var s = c.tape.get(i) || 'B';
      h += '<div class="case' + (s === 'B' ? ' blanc' : '') + (i === c.pos ? ' tete' : '') + '">' + esc(s) + '</div>';
    }
    conteneur.innerHTML = h;
  }

  /* ---------- Machine à quadruplets ---------- */
  function widgetTM(w) {
    var T = window.Turing, txt = source(w), quads;
    try { quads = T.parseQuads(txt); } catch (e) { w.textContent = e.message; return; }
    var M = new T.QuadMachine(quads);
    var titre = w.dataset.titre ? '<h5>' + esc(w.dataset.titre) + '</h5>' : '';
    w.innerHTML = titre +
      '<details' + (quads.length <= 30 ? ' open' : '') + '><summary>Programme : ' + quads.length + ' quadruplets</summary><div class="programme no-math"></div></details>' +
      '<div class="ligne"><label>Entrée (entiers) : <input type="text" size="12" class="arg"></label>' +
      '<button type="button" class="pas">Un pas</button><button type="button" class="principal tout">Exécuter</button><button type="button" class="raz">Réinitialiser</button></div>' +
      '<div class="bande"></div><div class="info"></div><details><summary>Descriptions instantanées successives</summary><div class="sortie no-math"></div></details>';
    w.querySelector('.programme').innerHTML = quads.map(function (q) { return '<div>' + esc(q.join(', ')) + '</div>'; }).join('');
    var inp = w.querySelector('.arg'); inp.value = w.dataset.args || '';
    var bande = w.querySelector('.bande'), info = w.querySelector('.info'), sortie = w.querySelector('.sortie');
    var c, trace;
    function raz() {
      try { c = M.start(parseArgs(inp.value)); } catch (e) { info.innerHTML = '<span class="ko">' + esc(e.message) + '</span>'; return; }
      trace = [T.describe(c)]; maj();
    }
    function maj() {
      dessinerBande(bande, c);
      var etat = c.halted ? '<span class="ok">arrêt</span> — résultat ⟨α⟩ = <b>' + T.countOnes(c) + '</b> (nombre de barres sur la bande)' : 'état <span class="etat">' + esc(c.state) + '</span>';
      info.innerHTML = 'Pas : ' + c.steps + ' — ' + etat;
      sortie.textContent = trace.join('\n') + (trace.length >= 400 ? '\n…' : '');
    }
    w.querySelector('.pas').onclick = function () { if (!c.halted) { T.QuadMachine.prototype.step.call(M, c); if (trace.length < 400) trace.push(T.describe(c)); if (!M.table[c.state + '\u0000' + (c.tape.get(c.pos) || 'B')]) c.halted = true; } maj(); };
    w.querySelector('.tout').onclick = function () {
      raz(); var lim = parseInt(w.dataset.max || '2000000', 10);
      while (c.steps < lim && M.step(c)) { if (trace.length < 400) trace.push(T.describe(c)); }
      if (!c.halted) info.innerHTML = 'Pas : ' + c.steps + ' — <span class="ko">pas d’arrêt après ' + lim + ' pas</span> (la machine ne s’arrête peut-être jamais)';
      else maj();
      if (!c.halted) dessinerBande(bande, c);
    };
    w.querySelector('.raz').onclick = raz;
    raz();
  }

  /* ---------- Compilateur fonctions récursives -> MT ---------- */
  var CATALOGUE = [
    ['add', 'Addition  x + y'], ['mult', 'Multiplication  x × y'], ['pred', 'Prédécesseur  x ∸ 1'],
    ['monus', 'Différence propre  x ∸ y'], ['sg', 'Signe  sg(x)'], ['sgbar', 'Test de nullité  sg barre(x)'], ['eq', 'Égalité  χ=(x, y)'],
    ['pow', 'Puissance  x^y'], ['fact', 'Factorielle  y!'], ['div', 'Quotient  ⌊x / y⌋ (minimisation, indéfini si y = 0)'],
    ['vide', 'Fonction partout indéfinie  μz[1]']
  ];
  var FORMULES = {
    add: '\\mathrm{add}=\\rho[A^{(1)}_1,\\ \\sigma[S, A^{(3)}_2]]',
    mult: '\\mathrm{mult}=\\rho[0^{(1)},\\ \\sigma[\\mathrm{add}, A^{(3)}_3, A^{(3)}_2]]',
    pred: '\\mathrm{pred}=\\rho[0^{(0)},\\ A^{(2)}_1]',
    monus: 'x\\monus y=\\sigma[\\rho[A^{(1)}_1,\\sigma[\\mathrm{pred},A^{(3)}_2]],\\ A^{(2)}_2, A^{(2)}_1](x,y)',
    sg: '\\mathrm{sg}=\\rho[0^{(0)},\\ 1^{(2)}]',
    div: '\\lfloor x/y\\rfloor=\\mu z\\,[\\,\\overline{\\mathrm{sg}}\\big(((z+1)\\times y)\\monus x\\big)=0\\,]',
    sgbar: '\\overline{\\mathrm{sg}}=\\rho[1^{(0)},\\ 0^{(2)}]',
    eq: '\\chi_=(x,y)=\\sigma[\\overline{\\mathrm{sg}},\\sigma[\\mathrm{add},\\monus,\\sigma[\\monus,A^{(2)}_2,A^{(2)}_1]]](x,y)',
    pow: 'x^y=\\sigma[\\rho[1^{(1)},\\sigma[\\mathrm{mult},A^{(3)}_3,A^{(3)}_2]],\\ A^{(2)}_2,A^{(2)}_1](x,y)',
    fact: '\\mathrm{fact}=\\rho[1^{(0)},\\ \\sigma[\\mathrm{mult},\\sigma[S,A^{(2)}_1],A^{(2)}_2]]',
    vide: '\\mu[1^{(2)}]'
  };
  function widgetCompil(w) {
    var T = window.Turing;
    var opts = CATALOGUE.map(function (c) { return '<option value="' + c[0] + '">' + esc(c[1]) + '</option>'; }).join('');
    w.innerHTML = '<h5>Compilateur : fonction récursive → machine de Turing complète</h5>' +
      '<div class="ligne"><label>Fonction : <select class="fn">' + opts + '</select></label>' +
      '<label>Entrée : <input type="text" size="8" class="arg" value="2, 3"></label>' +
      '<button type="button" class="principal go">Compiler et exécuter</button></div>' +
      '<div class="formule"></div><div class="info"></div>' +
      '<details><summary>Programme complet (quadruplets)</summary><div class="programme no-math"></div></details>';
    var sel = w.querySelector('.fn'); if (w.dataset.fn) sel.value = w.dataset.fn;
    if (w.dataset.args) w.querySelector('.arg').value = w.dataset.args;
    function go() {
      var f = T.lib[sel.value], info = w.querySelector('.info');
      var fm = w.querySelector('.formule');
      fm.innerHTML = '';
      if (window.katex) try { katex.render(FORMULES[sel.value], fm, { displayMode: true, throwOnError: false, macros: { '\\monus': '\\mathbin{\\dot{-}}' } }); } catch (e) {}
      var args;
      try { args = T.terms && parseArgs(w.querySelector('.arg').value); } catch (e) { info.innerHTML = '<span class="ko">' + esc(e.message) + '</span>'; return; }
      if (args.length !== T.arity(f)) { info.innerHTML = '<span class="ko">Cette fonction attend ' + T.arity(f) + ' argument(s).</span>'; return; }
      var tm = T.compileToTM(f), M = new T.QuadMachine(tm.quads);
      var c = M.run(args, 5e6);
      var attendu; try { attendu = T.evalTerm(f, args, { n: 2e5 }); } catch (e) { attendu = undefined; }
      var res = c.halted ? T.countOnes(c) : undefined;
      info.innerHTML = 'Machine produite : <b>' + tm.quads.length + '</b> quadruplets, <b>' + tm.states + '</b> états. ' +
        (c.halted ? 'Arrêt après <b>' + c.steps.toLocaleString('fr-FR') + '</b> pas, résultat <b>' + res + '</b>.' : 'Pas d’arrêt après ' + c.steps.toLocaleString('fr-FR') + ' pas (fonction indéfinie en ce point ?).') +
        ' Évaluation directe : ' + (attendu === undefined ? 'indéfinie (recherche sans fin)' : attendu) + '. ' +
        (res === attendu ? '<span class="ok">Concordance.</span>' : '<span class="ko">Désaccord !</span>');
      w.querySelector('.programme').innerHTML = tm.quads.map(function (q) { return '<div>' + esc(q.join(', ')) + '</div>'; }).join('');
    }
    w.querySelector('.go').onclick = go;
    go();
  }

  /* ---------- Castors affairés (quintuplets de Rado) ---------- */
  function widgetRado(w) {
    var T = window.Turing, txt = source(w), qs;
    try { qs = T.parseQuints(txt); } catch (e) { w.textContent = e.message; return; }
    w.innerHTML = (w.dataset.titre ? '<h5>' + esc(w.dataset.titre) + '</h5>' : '') +
      '<div class="programme no-math">' + qs.map(function (q) { return '<div>(' + esc(q.join(', ')) + ')</div>'; }).join('') + '</div>' +
      '<div class="ligne"><button type="button" class="principal go">Lancer sur une bande blanche</button></div><div class="info"></div><div class="bande"></div>';
    w.querySelector('.go').onclick = function () {
      var info = w.querySelector('.info');
      info.textContent = 'Calcul en cours…';
      setTimeout(function () {
        var t0 = performance.now();
        var r = T.runRado(qs, parseFloat(w.dataset.max || '1e8'));
        var dt = Math.round(performance.now() - t0);
        info.innerHTML = (r.halted ? '<span class="ok">Arrêt</span>' : '<span class="ko">Pas d’arrêt dans la limite</span>') +
          ' après <b>' + r.steps.toLocaleString('fr-FR') + '</b> pas ; <b>' + r.ones.toLocaleString('fr-FR') + '</b> symboles 1 sur la bande (' + dt + ' ms).';
        var b = w.querySelector('.bande');
        if (r.hi - r.lo < 80) {
          var h = '';
          for (var i = r.lo - 1; i <= r.hi + 1; i++) h += '<div class="case' + (r.tape[i] ? '' : ' blanc') + (i === r.pos ? ' tete' : '') + '">' + (r.tape[i] ? '1' : '0') + '</div>';
          b.innerHTML = h;
        } else b.innerHTML = '<span>(bande trop longue pour être dessinée : ' + (r.hi - r.lo + 1).toLocaleString('fr-FR') + ' cases visitées)</span>';
      }, 20);
    };
  }

  /* ---------- λ-calcul ---------- */
  function widgetLambda(w) {
    var L = window.Lambda, src = source(w);
    w.innerHTML = (w.dataset.titre ? '<h5>' + esc(w.dataset.titre) + '</h5>' : '') +
      '<textarea spellcheck="false" class="no-math"></textarea>' +
      '<div class="ligne"><button type="button" class="principal go">Réduire (ordre normal)</button><label>pas max : <input type="text" size="7" class="max" value="' + (w.dataset.max || '20000') + '"></label></div>' +
      '<div class="info"></div><details><summary>Premières étapes de réduction</summary><div class="sortie no-math"></div></details>';
    var ta = w.querySelector('textarea'); ta.value = src;
    ta.style.minHeight = Math.min(320, 26 + 20 * src.split('\n').length) + 'px';
    w.querySelector('.go').onclick = function () {
      var info = w.querySelector('.info'), out = w.querySelector('.sortie');
      try {
        var t = L.parseProgram(ta.value);
        var r = L.normalize(t, parseInt(w.querySelector('.max').value, 10) || 20000, 200000, true);
        var rec = L.recognize(r.term);
        info.innerHTML = r.normal
          ? '<span class="ok">Forme normale</span> atteinte en <b>' + r.steps + '</b> pas : <code>' + esc(L.print(r.term)) + '</code>' + (rec.length ? ' — ' + rec.join(', ') : '')
          : '<span class="ko">Pas de forme normale trouvée</span> (' + r.reason + ', ' + r.steps + ' pas). Le terme n’a peut-être pas de forme normale.';
        out.textContent = r.trace.map(function (s, i) { return i + '. ' + s; }).join('\n') + (r.steps >= r.trace.length ? '\n…' : '');
      } catch (e) { info.innerHTML = '<span class="ko">' + esc(e.message) + '</span>'; }
    };
    if (w.dataset.auto !== 'non') w.querySelector('.go').click();
  }

  function widgetPCP(w) {
    var P = window.PCP, src = source(w);
    w.innerHTML = (w.dataset.titre ? '<h5>' + esc(w.dataset.titre) + '</h5>' : '') +
      '<p class="aide">Un domino par ligne, sous la forme <code>haut/bas</code>.</p>' +
      '<textarea spellcheck="false" class="no-math"></textarea>' +
      '<div class="ligne"><button type="button" class="principal go">Chercher une solution</button></div><div class="info"></div>';
    var ta = w.querySelector('textarea'); ta.value = src;
    ta.style.minHeight = Math.min(240, 26 + 20 * src.split('\n').length) + 'px';
    var info = w.querySelector('.info');
    w.querySelector('.go').onclick = function () {
      try {
        var d = P.parse(ta.value), t0 = Date.now(), r = P.resoudre(d, 300000, 120);
        if (r.ok) {
          var h = r.suite.map(function (i) { return d[i - 1][0]; }), b = r.suite.map(function (i) { return d[i - 1][1]; });
          info.innerHTML = '<span class="ok">Solution</span> de longueur <b>' + r.suite.length + '</b> (la plus courte, ' + (Date.now() - t0) + ' ms) : ' +
            '<code>' + r.suite.join(', ') + '</code><div class="pcp-mots"><div>haut : <code>' + h.map(esc).join('·') + '</code></div><div>bas : <code>' + b.map(esc).join('·') + '</code></div></div>';
        } else if (r.exhaustif) {
          info.innerHTML = '<span class="ko">Aucune solution</span> : la recherche a parcouru toutes les configurations possibles (' + r.noeuds + ').';
        } else {
          info.innerHTML = '<span class="ko">Pas de solution trouvée</span> après ' + r.noeuds + ' configurations. Il peut ne pas y en avoir, ou elle peut être plus longue : aucun programme ne peut trancher dans tous les cas.';
        }
      } catch (e) { info.innerHTML = '<span class="ko">' + esc(e.message) + '</span>'; }
    };
    if (w.dataset.auto !== 'non') w.querySelector('.go').click();
  }

  function widgetArith(w) {
    var mode = w.dataset.mode || 'facteurs';
    var euclide = mode === 'euclide';
    w.innerHTML = (w.dataset.titre ? '<h5>' + esc(w.dataset.titre) + '</h5>' : '') +
      '<div class="ligne"><label>' + (euclide ? 'Entiers a, b : ' : 'Entier n : ') +
      '<input type="text" size="18" class="arg" value="' + esc(w.dataset.args || (euclide ? '1071, 462' : '360')) + '"></label>' +
      '<button type="button" class="principal go">' + (euclide ? 'Calculer le pgcd' : 'Décomposer') + '</button></div><div class="info"></div>';
    var inp = w.querySelector('.arg'), info = w.querySelector('.info');
    function big(s) { s = s.trim(); if (!/^\d+$/.test(s)) throw new Error('« ' + s + ' » n’est pas un entier naturel.'); return BigInt(s); }
    w.querySelector('.go').onclick = function () {
      try {
        var lignes = [];
        if (euclide) {
          var v = inp.value.split(/[,;\s]+/).filter(Boolean);
          if (v.length !== 2) throw new Error('Donnez deux entiers séparés par une virgule.');
          var a = big(v[0]), b = big(v[1]), a0 = a, b0 = b;
          if (a === 0n && b === 0n) throw new Error('pgcd(0, 0) n’est pas défini ici : tout entier divise 0.');
          // Bézout étendu : on maintient a = a0*u1 - b0*v1 (au signe près) via des coefficients relatifs
          var u0 = 1n, v0 = 0n, u1 = 0n, v1 = 1n, n = 0;
          while (b !== 0n && n < 500) {
            var q = a / b, r = a % b;
            lignes.push(a + ' = ' + b + ' × ' + q + ' + ' + r);
            var t1 = u0 - q * u1, t2 = v0 - q * v1; u0 = u1; v0 = v1; u1 = t1; v1 = t2;
            a = b; b = r; n++;
          }
          info.innerHTML = '<pre class="no-math">' + lignes.map(esc).join('\n') + '</pre>' +
            '<span class="ok">pgcd(' + a0 + ', ' + b0 + ') = ' + a + '</span> après ' + n + ' division' + (n > 1 ? 's' : '') +
            ' ; relation de Bézout : ' + a + ' = ' + a0 + ' × (' + u0 + ') + ' + b0 + ' × (' + v0 + ').';
        } else {
          var m = big(inp.value), m0 = m, fac = [], d = 2n, essais = 0;
          if (m < 2n) throw new Error('Donnez un entier au moins égal à 2 (1 est le produit vide de facteurs premiers).');
          while (d * d <= m && essais < 2000000) {
            essais++;
            if (m % d === 0n) { var e = 0; while (m % d === 0n) { m /= d; e++; } fac.push([d, e]); lignes.push('divisible par ' + d + (e > 1 ? ' (' + e + ' fois)' : '') + ' → reste ' + m); }
            d += (d === 2n ? 1n : 2n);
          }
          if (d * d <= m) throw new Error('Trop de divisions d’essai : le nombre a un trop grand facteur premier pour cette méthode naïve.');
          if (m > 1n) { fac.push([m, 1]); lignes.push(m + ' n’a pas de diviseur ≤ √' + m + ' : il est premier'); }
          var txt = fac.map(function (f) { return f[0] + (f[1] > 1 ? '^' + f[1] : ''); }).join(' × ');
          info.innerHTML = '<pre class="no-math">' + lignes.map(esc).join('\n') + '</pre>' +
            '<span class="ok">' + m0 + ' = ' + esc(txt) + '</span>' + (fac.length === 1 && fac[0][1] === 1 ? ' (nombre premier)' : '') + ' — ' + essais + ' divisions d’essai.';
        }
      } catch (e) { info.innerHTML = '<span class="ko">' + esc(e.message) + '</span>'; }
    };
    w.querySelector('.go').click();
  }

  function init() {
    document.querySelectorAll('.tm-widget, .compil-widget, .rado-widget, .lambda-widget, .pcp-widget, .arith-widget').forEach(function (w) { w.classList.add('widget'); });
    document.querySelectorAll('.arith-widget').forEach(widgetArith);
    document.querySelectorAll('.pcp-widget').forEach(widgetPCP);
    document.querySelectorAll('.tm-widget').forEach(widgetTM);
    document.querySelectorAll('.compil-widget').forEach(widgetCompil);
    document.querySelectorAll('.rado-widget').forEach(widgetRado);
    document.querySelectorAll('.lambda-widget').forEach(widgetLambda);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
