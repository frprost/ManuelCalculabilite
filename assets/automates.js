/* Automates cellulaires élémentaires (Wolfram) : diagramme espace-temps sur un canevas.
   Bord : la ligne est un anneau (les deux extrémités sont voisines). */
(function () {
  'use strict';
  function pas(ligne, regle) {
    var n = ligne.length, r = new Array(n);
    for (var i = 0; i < n; i++) {
      var v = (ligne[(i - 1 + n) % n] << 2) | (ligne[i] << 1) | ligne[(i + 1) % n];
      r[i] = (regle >> v) & 1;
    }
    return r;
  }
  function initiale(n, mode, graine) {
    var l = new Array(n).fill(0), x = graine >>> 0 || 1;
    if (mode === 'droite') l[n - 1] = 1;
    else if (mode === 'centre') l[n >> 1] = 1;
    else for (var i = 0; i < n; i++) { x ^= x << 13; x >>>= 0; x ^= x >>> 17; x ^= x << 5; x >>>= 0; l[i] = x & 1; }
    return l;
  }
  function tableHTML(regle) {
    var s = '';
    for (var v = 7; v >= 0; v--) {
      s += '<span style="display:inline-block;margin:2px 6px 2px 0;font-family:var(--mono)">' +
        ((v >> 2) & 1) + ((v >> 1) & 1) + (v & 1) + '→' + ((regle >> v) & 1) + '</span>';
    }
    return s;
  }
  function monter(el) {
    var regle0 = parseInt(el.getAttribute('data-regle') || '110', 10);
    var mode0 = el.getAttribute('data-depart') || 'droite';
    el.classList.add('widget');
    el.innerHTML =
      '<h5>' + (el.getAttribute('data-titre') || 'Automate cellulaire élémentaire') + '</h5>' +
      '<div class="ligne"><label>Règle (0 à 255) <input type="text" size="4" class="ac-regle" value="' + regle0 + '"></label>' +
      '<label>Départ <select class="ac-depart"><option value="droite">une cellule à droite</option>' +
      '<option value="centre">une cellule au centre</option><option value="hasard">au hasard</option></select></label>' +
      '<button type="button" class="principal ac-go">Dessiner</button></div>' +
      '<div class="ac-table" style="font-size:13px"></div>' +
      '<canvas class="ac-canvas" width="640" height="400" style="width:100%;height:auto;display:block;margin-top:8px;image-rendering:pixelated;border:1px solid var(--trait);border-radius:6px"></canvas>' +
      '<div class="ac-info" style="font-size:13px;color:var(--texte-2);margin-top:4px"></div>';
    el.querySelector('.ac-depart').value = mode0;
    var cv = el.querySelector('.ac-canvas'), ctx = cv.getContext('2d');
    function dessiner() {
      var regle = parseInt(el.querySelector('.ac-regle').value, 10);
      if (!(regle >= 0 && regle <= 255)) { el.querySelector('.ac-info').textContent = 'La règle doit être un entier de 0 à 255.'; return; }
      var mode = el.querySelector('.ac-depart').value;
      var n = 160, t = 100, c = 4;
      cv.width = n * c; cv.height = t * c;
      var st = getComputedStyle(el);
      var fond = st.getPropertyValue('--fond').trim() || '#fff', encre = st.getPropertyValue('--texte').trim() || '#000';
      ctx.fillStyle = fond; ctx.fillRect(0, 0, cv.width, cv.height); ctx.fillStyle = encre;
      var l = initiale(n, mode, 12345), vivantes = 0;
      for (var y = 0; y < t; y++) {
        for (var x = 0; x < n; x++) if (l[x]) { ctx.fillRect(x * c, y * c, c, c); vivantes++; }
        l = pas(l, regle);
      }
      el.querySelector('.ac-table').innerHTML = 'Table de la règle ' + regle + ' (gauche, centre, droite → nouvelle valeur) : ' + tableHTML(regle);
      el.querySelector('.ac-info').textContent = n + ' cellules (sur un anneau), ' + t + ' pas ; le temps s’écoule vers le bas. ' + vivantes + ' cellules à 1 dessinées.';
    }
    el.querySelector('.ac-go').addEventListener('click', dessiner);
    el.querySelector('.ac-regle').addEventListener('keydown', function (e) { if (e.key === 'Enter') dessiner(); });
    dessiner();
  }
  function init() { document.querySelectorAll('.ac-widget').forEach(monter); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
  if (typeof module !== 'undefined') module.exports = { pas: pas };
})();
