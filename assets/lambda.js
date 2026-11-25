/* lambda.js — réducteur de λ-termes (stratégie normale, gauche-externe)
   pour le manuel de calculabilité. Navigateur (window.Lambda) et Node.
   Syntaxe : λx.M ou \x.M ; λx y.M abrège λx.λy.M ; application à gauche ;
   les entiers 0, 1, 2, ... désignent les entiers de Church ;
   des définitions « NOM = terme » peuvent précéder l'expression.          */
(function (root) {
  'use strict';

  // ---------- Analyse syntaxique ----------
  function tokenize(s) {
    var toks = [], i = 0;
    while (i < s.length) {
      var c = s[i];
      if (/\s/.test(c)) { i++; continue; }
      if (c === '(' || c === ')' || c === '.') { toks.push(c); i++; continue; }
      if (c === '\\' || c === 'λ') { toks.push('λ'); i++; continue; }
      var m = /^[A-Za-z0-9_'?+*\-]+/.exec(s.slice(i));
      if (!m) throw new Error('Caractère inattendu : ' + c);
      toks.push(m[0]); i += m[0].length;
    }
    return toks;
  }
  // AST nommé : {k:'v', n} | {k:'l', n, b} | {k:'a', f, x}
  function parse(s) {
    var toks = tokenize(s), p = 0;
    function peek() { return toks[p]; }
    function term() {
      if (peek() === 'λ') {
        p++;
        var names = [];
        while (peek() && peek() !== '.') names.push(toks[p++]);
        if (peek() !== '.' || names.length === 0) throw new Error('Abstraction mal formée');
        p++;
        var body = term();
        for (var i = names.length - 1; i >= 0; i--) body = { k: 'l', n: names[i], b: body };
        return body;
      }
      var t = atom();
      while (peek() !== undefined && peek() !== ')') {
        if (peek() === 'λ') { t = { k: 'a', f: t, x: term() }; break; }
        t = { k: 'a', f: t, x: atom() };
      }
      return t;
    }
    function atom() {
      var t = toks[p];
      if (t === '(') { p++; var e = term(); if (toks[p] !== ')') throw new Error('Parenthèse manquante'); p++; return e; }
      if (t === undefined || t === ')' || t === '.') throw new Error('Terme attendu');
      p++;
      return { k: 'v', n: t };
    }
    var r = term();
    if (p !== toks.length) throw new Error('Symbole en trop : ' + toks[p]);
    return r;
  }

  function church(n) {
    var b = { k: 'v', n: 'x' };
    for (var i = 0; i < n; i++) b = { k: 'a', f: { k: 'v', n: 'f' }, x: b };
    return { k: 'l', n: 'f', b: { k: 'l', n: 'x', b: b } };
  }

  // ---------- Indices de de Bruijn ----------
  // {k:'b', i} variable liée ; {k:'f', n} variable libre ; {k:'l', n, b} ; {k:'a', f, x}
  function toDB(t, env, defs, depth) {
    depth = depth || 0;
    if (depth > 200) throw new Error('Définitions récursives ?');
    switch (t.k) {
      case 'v': {
        var i = env.lastIndexOf(t.n);
        if (i >= 0) return { k: 'b', i: env.length - 1 - i };
        if (defs && Object.prototype.hasOwnProperty.call(defs, t.n)) return toDB(defs[t.n], [], defs, depth + 1);
        if (/^[0-9]+$/.test(t.n)) return toDB(church(parseInt(t.n, 10)), [], null);
        return { k: 'f', n: t.n };
      }
      case 'l': return { k: 'l', n: t.n, b: toDB(t.b, env.concat([t.n]), defs, depth) };
      case 'a': return { k: 'a', f: toDB(t.f, env, defs, depth), x: toDB(t.x, env, defs, depth) };
    }
  }
  function shift(t, d, c) {
    switch (t.k) {
      case 'b': return t.i >= c ? { k: 'b', i: t.i + d } : t;
      case 'f': return t;
      case 'l': return { k: 'l', n: t.n, b: shift(t.b, d, c + 1) };
      case 'a': return { k: 'a', f: shift(t.f, d, c), x: shift(t.x, d, c) };
    }
  }
  function subst(t, j, s) {
    switch (t.k) {
      case 'b': return t.i === j ? shift(s, j, 0) : (t.i > j ? { k: 'b', i: t.i - 1 } : t);
      case 'f': return t;
      case 'l': return { k: 'l', n: t.n, b: subst(t.b, j + 1, s) };
      case 'a': return { k: 'a', f: subst(t.f, j, s), x: subst(t.x, j, s) };
    }
  }
  function beta(lam, arg) { return subst(lam.b, 0, arg); }

  // Un pas de réduction en ordre normal ; renvoie null si forme normale
  function stepNormal(t) {
    if (t.k === 'a') {
      if (t.f.k === 'l') return beta(t.f, t.x);
      var f2 = stepNormal(t.f);
      if (f2) return { k: 'a', f: f2, x: t.x };
      var x2 = stepNormal(t.x);
      if (x2) return { k: 'a', f: t.f, x: x2 };
      return null;
    }
    if (t.k === 'l') { var b2 = stepNormal(t.b); return b2 ? { k: 'l', n: t.n, b: b2 } : null; }
    return null;
  }
  function size(t) {
    switch (t.k) { case 'b': case 'f': return 1; case 'l': return 1 + size(t.b); case 'a': return 1 + size(t.f) + size(t.x); }
  }

  // ---------- Affichage ----------
  function freeNames(t, acc) {
    acc = acc || {};
    if (t.k === 'f') acc[t.n] = true;
    else if (t.k === 'l') freeNames(t.b, acc);
    else if (t.k === 'a') { freeNames(t.f, acc); freeNames(t.x, acc); }
    return acc;
  }
  function print(t) {
    var free = freeNames(t);
    function fresh(hint, env) {
      var n = hint;
      while (free[n] || env.indexOf(n) >= 0) n = n + "'";
      return n;
    }
    function go(t, env, ctx) { // ctx : 0 = sommet, 1 = fonction d'une application, 2 = argument
      switch (t.k) {
        case 'b': return env[env.length - 1 - t.i];
        case 'f': return t.n;
        case 'l': {
          var names = [], cur = t, e = env.slice();
          while (cur.k === 'l') { var n = fresh(cur.n, e); names.push(n); e.push(n); cur = cur.b; }
          var s = 'λ' + names.join(' ') + '.' + go(cur, e, 0);
          return ctx === 0 ? s : '(' + s + ')';
        }
        case 'a': {
          var s2 = go(t.f, env, 1) + ' ' + go(t.x, env, 2);
          return ctx === 2 ? '(' + s2 + ')' : s2;
        }
      }
    }
    return go(t, [], 0);
  }
  // Reconnaît un entier de Church ou un booléen
  function recognize(t) {
    var out = [];
    if (t.k === 'l' && t.b.k === 'l') {
      var b = t.b.b, n = 0;
      while (b.k === 'a' && b.f.k === 'b' && b.f.i === 1) { n++; b = b.x; }
      if (b.k === 'b' && b.i === 0) out.push('entier de Church ' + n);
      if (t.b.b.k === 'b' && t.b.b.i === 1) out.push('booléen tt (vrai)');
      if (t.b.b.k === 'b' && t.b.b.i === 0) out.push('booléen ff (faux)');
    }
    return out;
  }

  function parseProgram(src) {
    var defs = {}, expr = null;
    src.split(/\n/).forEach(function (line) {
      line = line.replace(/--.*$/, '').trim();
      if (!line) return;
      var m = /^([^\s=()λ\\.]+)\s*=\s*(.+)$/.exec(line);
      if (m) defs[m[1]] = parse(m[2]);
      else expr = expr === null ? line : expr + ' ' + line;
    });
    if (expr === null) throw new Error('Aucune expression à réduire');
    return toDB(parse(expr), [], defs);
  }
  function normalize(t, maxSteps, maxSize, trace) {
    maxSteps = maxSteps || 10000; maxSize = maxSize || 200000;
    var steps = 0, tr = trace ? [print(t)] : null;
    while (steps < maxSteps) {
      var n = stepNormal(t);
      if (!n) return { term: t, steps: steps, normal: true, trace: tr };
      t = n; steps++;
      if (tr && tr.length < 60) tr.push(print(t));
      if (size(t) > maxSize) return { term: t, steps: steps, normal: false, reason: 'terme trop gros', trace: tr };
    }
    return { term: t, steps: steps, normal: false, reason: 'limite de pas atteinte', trace: tr };
  }
  function equalDB(a, b) {
    if (a.k !== b.k) return false;
    switch (a.k) {
      case 'b': return a.i === b.i; case 'f': return a.n === b.n;
      case 'l': return equalDB(a.b, b.b);
      case 'a': return equalDB(a.f, b.f) && equalDB(a.x, b.x);
    }
  }

  var api = { parse: parse, toDB: toDB, parseProgram: parseProgram, normalize: normalize, print: print,
    recognize: recognize, church: church, equalDB: equalDB, stepNormal: stepNormal };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.Lambda = api;
})(this);
