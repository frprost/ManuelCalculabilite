/* Recherche de solutions du problème de correspondance de Post (parcours en largeur).
   Une configuration est le « surplus » d'un côté sur l'autre ; on s'arrête quand il est vide. */
(function (root) {
  'use strict';
  function parse(text) {
    var dom = [];
    text.split('\n').forEach(function (l) {
      l = l.replace(/#.*$/, '').trim();
      if (!l) return;
      var p = l.split('/');
      if (p.length !== 2 || !p[0].trim() || !p[1].trim()) throw new Error('Domino mal formé : « ' + l + ' » (écrire haut/bas)');
      dom.push([p[0].trim(), p[1].trim()]);
    });
    if (!dom.length) throw new Error('Aucun domino.');
    return dom;
  }
  // étend un surplus (côté s : 0 = haut en avance, 1 = bas en avance) par le domino d
  function etendre(surplus, cote, d) {
    var h = (cote === 0 ? surplus : '') + d[0], b = (cote === 1 ? surplus : '') + d[1];
    var n = Math.min(h.length, b.length);
    if (h.slice(0, n) !== b.slice(0, n)) return null;
    return h.length >= b.length ? [h.slice(n), 0] : [b.slice(n), 1];
  }
  function resoudre(dom, maxNoeuds, maxSurplus) {
    maxNoeuds = maxNoeuds || 200000; maxSurplus = maxSurplus || 80;
    var file = [], vus = {}, tete = 0, coupe = false;
    for (var i = 0; i < dom.length; i++) {
      var e = etendre('', 0, dom[i]);
      if (!e) continue;
      if (e[0] === '') return { ok: true, suite: [i + 1], noeuds: 1 };
      var k = e[1] + ':' + e[0];
      if (!vus[k]) { vus[k] = true; file.push({ s: e[0], c: e[1], suite: [i + 1] }); }
    }
    while (tete < file.length) {
      if (file.length > maxNoeuds) { coupe = true; break; }
      var x = file[tete++];
      for (var j = 0; j < dom.length; j++) {
        var f = etendre(x.s, x.c, dom[j]);
        if (!f) continue;
        var suite = x.suite.concat([j + 1]);
        if (f[0] === '') return { ok: true, suite: suite, noeuds: file.length };
        if (f[0].length > maxSurplus) { coupe = true; continue; }
        var key = f[1] + ':' + f[0];
        if (vus[key]) continue;
        vus[key] = true; file.push({ s: f[0], c: f[1], suite: suite });
      }
    }
    return { ok: false, exhaustif: !coupe, noeuds: file.length };
  }
  var api = { parse: parse, resoudre: resoudre };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.PCP = api;
})(this);
