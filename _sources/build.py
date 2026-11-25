#!/usr/bin/env python3
"""Assemble le manuel : python3 _sources/build.py  (depuis le dossier du site).

Chaque page source (_sources/pages/*.html) commence par un en-tête :
    <!--
    titre: ...
    court: ...        (libellé du sommaire)
    chapo: ...        (facultatif)
    prerequis: a.html|Libellé ; b.html|Libellé   (facultatif)
    -->
Balises de commodité reconnues dans le corps :
    <res type="Théorème" nom="..." id="..."> <enonce>..</enonce>
         <philo>..</philo> <tech>..</tech> <techno>..</techno> </res>
    <err>..</err>  (correction de l'ébauche)    <preuve>..</preuve>
"""
import html
import os
import re
import unicodedata

import sys
ICI = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(ICI)
# Par défaut : version propre, sans encadrés de correction ni page des corrections.
# Version annotée (encadrés et page errata) : python3 build.py --annote DOSSIER
# (les assets doivent être copiés à part dans DOSSIER)
DIFFUSION = "--annote" not in sys.argv
if "--annote" in sys.argv:
    SITE = os.path.abspath(sys.argv[sys.argv.index("--annote") + 1])
elif "--diffusion" in sys.argv:
    SITE = os.path.abspath(sys.argv[sys.argv.index("--diffusion") + 1])

# (fichier, groupe) dans l'ordre de lecture
PAGES = [
    ("index.html", None),
    ("motivations.html", "Entrer dans le sujet"),
    ("trois-approches.html", "Entrer dans le sujet"),
    ("machines-turing.html", "Modèles de calcul"),
    ("fonctions-recursives.html", "Modèles de calcul"),
    ("lambda-calcul.html", "Modèles de calcul"),
    ("equivalence.html", "Modèles de calcul"),
    ("these-church.html", "Modèles de calcul"),
    ("universalite.html", "Théorèmes fondamentaux"),
    ("smn-recursion.html", "Théorèmes fondamentaux"),
    ("indecidabilite.html", "Limites du calcul"),
    ("semi-decidabilite.html", "Limites du calcul"),
    ("hierarchie-arithmetique.html", "Limites du calcul"),
    ("incompletude.html", "Limites du calcul"),
    ("equations-diophantiennes.html", "Limites du calcul"),
    ("logique-types.html", "Limites du calcul"),
    ("theories-decidables.html", "Limites du calcul"),
    ("mathematiques-indecidables.html", "Limites du calcul"),
    ("kolmogorov-omega.html", "Limites du calcul"),
    ("langages.html", "Limites du calcul"),
    ("complexite.html", "Complexité"),
    ("hasard-quantique.html", "Complexité"),
    ("ackermann.html", "Études de cas"),
    ("castors-affaires.html", "Études de cas"),
    ("calculabilite-ia.html", "Études de cas"),
    ("autres-modeles.html", "Études de cas"),
    ("parcours.html", "Annexes"),
    ("cantor.html", "Annexes"),
    ("bases.html", "Annexes"),
    ("leibniz.html", "Annexes"),
    ("errata.html", "Annexes"),
    ("bibliographie.html", "Annexes"),
]

if DIFFUSION:
    PAGES = [p for p in PAGES if p[0] != "errata.html"]

TYPES_DEF = {"Définition", "Notation", "Convention", "Exemple"}


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\$[^$]*\$", "", s)
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "section"


def lire_page(nom):
    with open(os.path.join(ICI, "pages", nom), encoding="utf-8") as f:
        src = f.read()
    m = re.match(r"\s*<!--(.*?)-->", src, re.S)
    meta = {}
    if m:
        for ligne in m.group(1).strip().splitlines():
            if ":" in ligne:
                k, v = ligne.split(":", 1)
                meta[k.strip()] = v.strip()
        src = src[m.end():]
    return meta, src


def attr(s, nom):
    m = re.search(nom + r'="([^"]*)"', s)
    return m.group(1) if m else ""


def echapper_maths(corps):
    """Dans les formules $...$ et $$...$$, « <A » serait lu comme une balise HTML : on écrit &lt;."""
    return re.sub(r"\$\$.*?\$\$|\$[^$\n]+?\$",
                  lambda m: re.sub(r"<(?=[A-Za-z/!])", "&lt;", m.group(0)), corps, flags=re.S)


def transformer(corps, page, index_res):
    if DIFFUSION:
        corps = re.sub(r"<err(?:\s[^>]*)?>.*?</err>\s*", "", corps, flags=re.S)
        corps = re.sub(r"<brouillon>.*?</brouillon>", "", corps, flags=re.S)
        corps = corps.replace("<diffusion>", "").replace("</diffusion>", "")
    else:
        corps = re.sub(r"<diffusion>.*?</diffusion>", "", corps, flags=re.S)
        corps = corps.replace("<brouillon>", "").replace("</brouillon>", "")
    corps = echapper_maths(corps)
    def res(m):
        a = m.group(1)
        typ, nom, ident = attr(a, "type") or "Théorème", attr(a, "nom"), attr(a, "id")
        if not ident:
            ident = slug(nom)
        index_res.append((nom, typ, page, ident))
        cls = "definition" if typ in TYPES_DEF else "theoreme"
        return ('<div class="resultat %s" id="%s"><div class="entete-res"><div class="type">%s</div>'
                '<div class="nom">%s</div></div>' % (cls, ident, typ, nom))
    corps = re.sub(r"<res\b([^>]*)>", res, corps)
    corps = corps.replace("</res>", "</div>")
    corps = re.sub(r"<enonce>", '<div class="enonce">', corps)
    for n in ("philo", "tech", "techno"):
        corps = re.sub(r"<%s>" % n, '<div class="niveau" data-niveau="%s">' % n, corps)
    corps = re.sub(r"</(enonce|philo|tech|techno)>", "</div>", corps)
    corps = re.sub(r"<err((?:\s[^>]*)?)>", lambda m: '<div class="erreur-ebauche" data-src="%s">' % (attr(m.group(1) or "", "src") or "ebauche"), corps).replace("</err>", "</div>")
    corps = re.sub(r"<preuve>", '<div class="preuve">', corps).replace("</preuve>", "</div>")
    # exercices : <exo niveau="1|2|3" titre="..." id="..."> énoncé <corrige>...</corrige> </exo>
    compteur = [0]
    def exo(m):
        a = m.group(1)
        compteur[0] += 1
        niv = int(attr(a, "niveau") or "1")
        ident = attr(a, "id") or "exercice-%d" % compteur[0]
        t = attr(a, "titre")
        legende = ""
        if compteur[0] == 1:
            legende = ('<p class="legende-exo">Niveaux : ★ application directe du cours, ★★ exercice standard, '
                       '★★★ approfondissement. Les corrections sont masquées : cliquer sur « Correction » pour les afficher.</p>')
        return ('%s<div class="exercice" id="%s"><div class="entete-exo"><span class="etoiles" title="niveau %d">%s</span>'
                '<span class="nom-exo">Exercice %d%s</span></div><div class="corps-exo">'
                % (legende, ident, niv, "★" * niv, compteur[0], (" — " + t) if t else ""))
    corps = re.sub(r"<exo\b([^>]*)>", exo, corps)
    corps = corps.replace("</exo>", "</div></div>")
    corps = corps.replace("<corrige>", '<details class="corrige"><summary>Correction</summary><div class="texte-corrige">')
    corps = corps.replace("</corrige>", "</div></details>")
    # identifiants des sections h2/h3
    toc = []
    vus = set()

    def titre(m):
        niv, attrs, txt = m.group(1), m.group(2), m.group(3)
        ident = attr(attrs, "id") or slug(txt)
        base, k = ident, 2
        while ident in vus:
            ident = "%s-%d" % (base, k)
            k += 1
        vus.add(ident)
        if niv == "2":
            toc.append((ident, re.sub(r"<[^>]+>", "", txt)))
        return '<h%s id="%s">%s</h%s>' % (niv, ident, txt, niv)
    corps = re.sub(r"<h([23])((?:\s[^>]*)?)>(.*?)</h\1>", titre, corps, flags=re.S)
    return corps, toc


def gabarit(meta, corps, toc, nom, precedent, suivant, sommaire):
    titre = meta.get("titre", "")
    tete_titre = "Calculabilité" if nom == "index.html" else titre + " · Calculabilité"
    prereq = ""
    if meta.get("prerequis"):
        liens = []
        for item in meta["prerequis"].split(";"):
            if "|" in item:
                f, l = item.split("|", 1)
                liens.append('<a href="%s">%s</a>' % (f.strip(), l.strip()))
            else:
                liens.append(item.strip())
        prereq = '<div class="prerequis"><strong>Pré-requis</strong>%s</div>' % " · ".join(liens)
    toc_html = ""
    if len(toc) >= 3 and nom != "index.html":
        toc_html = '<nav class="toc-locale" aria-label="Dans ce chapitre"><strong>Dans ce chapitre</strong><ol>%s</ol></nav>' % "".join(
            '<li><a href="#%s">%s</a></li>' % (i, t) for i, t in toc)
    nav = '<nav class="nav-chap">'
    if precedent:
        nav += '<a href="%s"><small>← Précédent</small>%s</a>' % precedent
    else:
        nav += "<span></span>"
    if suivant:
        nav += '<a href="%s" style="text-align:right"><small>Suivant →</small>%s</a>' % suivant
    nav += "</nav>"
    chapo = '<p class="chapo">%s</p>' % meta["chapo"] if meta.get("chapo") else ""
    return """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="author" content="Frédéric Prost et Claude">
<title>{tete_titre}</title>
<link rel="stylesheet" href="assets/katex/katex.min.css">
<link rel="stylesheet" href="assets/style.css">
<script>try{{var t=localStorage.getItem('calc-theme');if(t)document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}document.documentElement.classList.add('js');</script>
</head>
<body>
<header class="entete"><div class="entete-int">
  <button type="button" class="btn-menu" aria-label="Sommaire">☰ Sommaire</button>
  <a class="titre-site" href="index.html">Calculabilité <span>·</span> un manuel à trois niveaux</a>
  <span class="selecteur-legende">Niveau de lecture :</span>
  <div class="selecteur" role="group" aria-label="Niveau de lecture">
    <button type="button" data-niveau="philo" title="Sens et implications">Philosophique</button>
    <button type="button" data-niveau="tech" title="Preuves mathématiques">Technique</button>
    <button type="button" data-niveau="techno" title="Constructions complètes, machines de Turing">Technologique</button>
    <button type="button" data-niveau="tout" title="Afficher les trois niveaux">Tout</button>
  </div>
  <button type="button" class="btn-theme" aria-label="Changer de thème" title="Clair / sombre">◐</button>
</div></header>
<div class="page">
<nav class="sommaire" aria-label="Sommaire">{sommaire}</nav>
<main class="contenu">
<h1>{titre}</h1>
{chapo}
{prereq}
{toc}
{corps}
{nav}
<footer class="pied">Calculabilité — manuel à trois niveaux de lecture. {credit} Texte sous licence <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.fr" rel="license">CC BY-SA 4.0</a>, code sous licence MIT. Les mathématiques sont rendues par KaTeX (licence MIT), embarqué localement : le site se lit sans connexion.</footer>
</main>
</div>
<script src="assets/katex/katex.min.js"></script>
<script src="assets/katex/contrib/auto-render.min.js"></script>
<script src="assets/turing.js"></script>
<script src="assets/lambda.js"></script>
<script src="assets/pcp.js"></script>
<script src="assets/automates.js"></script>
<script src="assets/niveaux.js"></script>
<script src="assets/widgets.js"></script>
</body>
</html>
""".format(tete_titre=html.escape(tete_titre), titre=titre, chapo=chapo, prereq=prereq, toc=toc_html,
           corps=corps, nav=nav, sommaire=sommaire,
           credit="Auteurs : Frédéric Prost et Claude." if DIFFUSION else "Auteurs : Frédéric Prost et Claude. Première version HTML d’après l’ébauche de Frédéric Prost (2020), les notes de cours (2021) et le polycopié de Ch. Boitet, complétée et vérifiée.")


SOURCES_ERR = [
    ("ebauche", "Ébauche du manuel (PDF)", "dans l’ébauche"),
    ("notes", "Notes de cours « Modèles de calcul » (F. Prost, 2021)", "dans les notes de cours"),
    ("boitet", "Polycopié « Récursivité, calculabilité » (Ch. Boitet, 1983-1987)", "dans le polycopié de Ch. Boitet"),
]


def collecter_errata(sources, metas):
    """Rassemble toutes les corrections <err> des pages, par document source, avec un lien vers leur contexte."""
    par_source = {k: [] for k, _, _ in SOURCES_ERR}
    for nom, _ in PAGES:
        if nom == "errata.html":
            continue
        ctx_id, ctx_nom = "", metas[nom]["titre"]
        for m in re.finditer(r"<res\b([^>]*)>|<h2([^>]*)>(.*?)</h2>|<err((?:\s[^>]*)?)>(.*?)</err>", sources[nom], flags=re.S):
            if m.group(1) is not None:
                ctx_id = attr(m.group(1), "id") or slug(attr(m.group(1), "nom"))
                ctx_nom = attr(m.group(1), "nom")
            elif m.group(3) is not None:
                ctx_id = attr(m.group(2) or "", "id") or slug(m.group(3))
                ctx_nom = re.sub(r"<[^>]+>", "", m.group(3))
            else:
                src = attr(m.group(4) or "", "src") or "ebauche"
                par_source[src].append((nom, '<li><p class="contexte"><a href="%s#%s">%s</a></p>%s</li>' % (nom, ctx_id, ctx_nom, m.group(5).strip())))
    h, resume = "", []
    for k, titre, court in SOURCES_ERR:
        items = par_source[k]
        if not items:
            continue
        resume.append("%d %s" % (len(items), court))
        h += '<h2 id="src-%s">%s</h2>' % (k, titre)
        page = None
        for nom, li in items:
            if nom != page:
                if page is not None:
                    h += "</ol>"
                h += '<h3>%s</h3><ol class="errata">' % metas[nom]["titre"]
                page = nom
            h += li
        h += "</ol>"
    total = sum(len(v) for v in par_source.values())
    return '<p><strong>%d corrections</strong> : %s.</p>' % (total, ", ".join(resume)) + h


def construire():
    metas = {}
    sources = {}
    for nom, _ in PAGES:
        metas[nom], sources[nom] = lire_page(nom)
    # sommaire
    def sommaire(actif):
        h, groupe, num = "", None, 0
        h += '<ul><li><a href="index.html"%s>Accueil et mode d’emploi</a></li></ul>' % (
            ' aria-current="page"' if actif == "index.html" else "")
        for nom, g in PAGES[1:]:
            if g != groupe:
                if groupe is not None:
                    h += "</ol>"
                h += "<h2>%s</h2><ol>" % g
                groupe = g
            court = metas[nom].get("court") or metas[nom].get("titre")
            pref = ""
            if g != "Annexes":
                num += 1
                pref = '<span class="num">%d</span>' % num
            h += '<li><a href="%s"%s>%s%s</a></li>' % (nom, ' aria-current="page"' if nom == actif else "", pref, court)
        return h + "</ol>"
    index_res = []
    rendus = {}
    if not DIFFUSION:
      sources["errata.html"] = sources["errata.html"].replace("<!--ERRATA-->", collecter_errata(sources, metas))
    for nom, _ in PAGES:
        corps, toc = transformer(sources[nom], nom, index_res)
        rendus[nom] = (corps, toc)
    # index alphabétique des résultats, injecté dans l'accueil
    def cle(t):
        return unicodedata.normalize("NFKD", re.sub(r"<[^>]+>|\$", "", t[0])).encode("ascii", "ignore").decode().lower()
    alpha = "".join('<li><a href="%s#%s">%s</a> <small>(%s)</small></li>' % (p, i, n, t.lower())
                    for n, t, p, i in sorted(index_res, key=cle))
    corps, toc = rendus["index.html"]
    corps = corps.replace("<!--INDEX-ALPHA-->", '<ul class="alpha">%s</ul>' % alpha)
    themes = ""
    groupe = None
    for nom, g in PAGES[1:]:
        if g != groupe:
            if groupe is not None:
                themes += "</ul></div>"
            themes += '<div class="carte"><h4>%s</h4><ul>' % g
            groupe = g
        themes += '<li><a href="%s">%s</a></li>' % (nom, metas[nom].get("court") or metas[nom]["titre"])
    themes += "</ul></div>"
    corps = corps.replace("<!--THEMES-->", '<div class="cartes">%s</div>' % themes)
    rendus["index.html"] = (corps, toc)
    for k, (nom, _) in enumerate(PAGES):
        prec = (PAGES[k - 1][0], metas[PAGES[k - 1][0]]["titre"]) if k > 0 else None
        suiv = (PAGES[k + 1][0], metas[PAGES[k + 1][0]]["titre"]) if k + 1 < len(PAGES) else None
        corps, toc = rendus[nom]
        sortie = gabarit(metas[nom], corps, toc, nom, prec, suiv, sommaire(nom))
        with open(os.path.join(SITE, nom), "w", encoding="utf-8") as f:
            f.write(sortie)
    print("%d pages, %d résultats indexés" % (len(PAGES), len(index_res)))


if __name__ == "__main__":
    construire()
