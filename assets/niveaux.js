/* niveaux.js — niveaux de lecture, onglets, thème, rendu des mathématiques */
(function () {
  'use strict';
  var doc = document.documentElement;
  doc.classList.add('js');
  var NOMS = { philo: 'Philosophique', tech: 'Technique', techno: 'Technologique' };
  var ORDRE = ['philo', 'tech', 'techno'];

  function lire(cle, defaut) { try { return localStorage.getItem(cle) || defaut; } catch (e) { return defaut; } }
  function ecrire(cle, v) { try { localStorage.setItem(cle, v); } catch (e) { /* stockage indisponible */ } }

  // Thème appliqué au plus tôt
  var theme = lire('calc-theme', '');
  if (theme) doc.setAttribute('data-theme', theme);

  function appliquerGlobal(n) {
    doc.classList.remove('tout', 'n-philo', 'n-tech', 'n-techno');
    if (n === 'tout') doc.classList.add('tout'); else doc.classList.add('n-' + n);
    document.querySelectorAll('.selecteur button').forEach(function (b) {
      b.setAttribute('aria-pressed', b.dataset.niveau === n ? 'true' : 'false');
    });
    document.querySelectorAll('.resultat').forEach(function (r) { choisir(r, n === 'tout' ? null : n); });
  }

  function choisir(res, n) {
    var dispo = Array.prototype.map.call(res.querySelectorAll(':scope > .niveau'), function (d) { return d.dataset.niveau; });
    if (!n || dispo.indexOf(n) < 0) {
      // niveau absent : on prend le plus proche (technique par défaut)
      n = dispo.indexOf('tech') >= 0 ? 'tech' : dispo[0];
    }
    res.querySelectorAll(':scope > .niveau').forEach(function (d) { d.classList.toggle('actif', d.dataset.niveau === n); });
    // au niveau philosophique, le récit en clair remplace l'énoncé formel
    res.classList.toggle('vue-philo', n === 'philo' && !doc.classList.contains('tout'));
    res.querySelectorAll(':scope > .onglets button').forEach(function (b) { b.setAttribute('aria-selected', b.dataset.niveau === n ? 'true' : 'false'); });
  }

  function preparerResultats() {
    document.querySelectorAll('.resultat').forEach(function (res, k) {
      var niveaux = res.querySelectorAll(':scope > .niveau');
      if (!niveaux.length) return;
      var barre = document.createElement('div');
      barre.className = 'onglets';
      barre.setAttribute('role', 'tablist');
      ORDRE.forEach(function (n) {
        var d = res.querySelector(':scope > .niveau[data-niveau="' + n + '"]');
        if (!d) return;
        var t = document.createElement('div');
        t.className = 'niveau-titre';
        t.textContent = 'Niveau ' + NOMS[n].toLowerCase();
        d.insertBefore(t, d.firstChild);
        var b = document.createElement('button');
        b.type = 'button'; b.dataset.niveau = n; b.setAttribute('role', 'tab');
        b.innerHTML = '<span class="pastille ' + n + '"></span>' + NOMS[n];
        b.addEventListener('click', function () { choisir(res, n); });
        barre.appendChild(b);
      });
      niveaux[0].parentNode.insertBefore(barre, niveaux[0]);
    });
  }

  function init() {
    preparerResultats();
    var n = lire('calc-niveau', 'tech');
    document.querySelectorAll('.selecteur button').forEach(function (b) {
      b.addEventListener('click', function () { ecrire('calc-niveau', b.dataset.niveau); appliquerGlobal(b.dataset.niveau); });
    });
    appliquerGlobal(n);
    // Ouvrir l'onglet visé par une ancre (#id-niveau-techno)
    var h = location.hash.match(/^#(.+)-(philo|tech|techno)$/);
    if (h) { var r = document.getElementById(h[1]); if (r) { choisir(r, h[2]); r.scrollIntoView(); } }

    var bt = document.querySelector('.btn-theme');
    if (bt) bt.addEventListener('click', function () {
      var sombre = doc.getAttribute('data-theme') === 'dark' ||
        (!doc.getAttribute('data-theme') && window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches);
      var nv = sombre ? 'light' : 'dark';
      doc.setAttribute('data-theme', nv); ecrire('calc-theme', nv);
    });
    var bm = document.querySelector('.btn-menu');
    if (bm) bm.addEventListener('click', function () { document.querySelector('.sommaire').classList.toggle('ouvert'); });

    if (window.renderMathInElement) {
      renderMathInElement(document.body, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '\\[', right: '\\]', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false }
        ],
        ignoredClasses: ['programme', 'sortie', 'no-math'],
        ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'option'],
        throwOnError: false, strict: false,
        macros: {
          '\\N': '\\mathbb{N}', '\\R': '\\mathbb{R}', '\\ind': '\\uparrow', '\\conv': '\\downarrow',
          '\\monus': '\\mathbin{\\dot{-}}', '\\RP': '\\mathcal{RP}', '\\PR': '\\mathcal{P}'
        }
      });
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
