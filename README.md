# Calculabilité — manuel à trois niveaux de lecture

Auteurs : **Frédéric Prost et Claude**.

Ce qu’une machine peut calculer, ce qu’aucune ne pourra jamais calculer, et pourquoi cela nous concerne tous. Le manuel est un site HTML statique : chaque résultat se lit à trois niveaux (l’énoncé, une explication intuitive, la démonstration complète), avec des programmes et des simulations exécutables.

## Lire le manuel

Ouvrir `index.html` dans un navigateur. Aucun serveur ni connexion n’est nécessaire : KaTeX est embarqué dans `assets/katex/`. Le site peut aussi être publié tel quel, par exemple avec GitHub Pages (branche principale, dossier racine).

## Contenu

- 25 chapitres, de la machine de Turing à la complexité, au hasard et au calcul quantique, puis des études de cas (fonction d’Ackermann, castors affairés, calculabilité et IA, autres modèles de calcul) ;
- des annexes : parcours de lecture, argument de Cantor, notions de base, Leibniz, bibliographie ;
- des exercices corrigés à la fin de chaque chapitre ;
- les programmes Python cités dans le texte, dans `assets/code/` ; chacun s’exécute avec `python3 fichier.py` et vérifie ce qu’il affirme.

Les résultats énoncés sans démonstration sont signalés « cité pour information ».

## Organisation des fichiers

| Chemin | Rôle |
|---|---|
| `*.html` | pages produites (à ne pas modifier à la main) |
| `_sources/pages/*.html` | sources des pages, avec un en-tête (titre, sommaire, prérequis) |
| `_sources/build.py` | assemblage : gabarit, sommaire, numérotation, liens précédent/suivant |
| `assets/style.css` | mise en page (thème clair et sombre) |
| `assets/*.js` | simulateurs interactifs (machines de Turing, λ-calcul, Post, automates cellulaires) |
| `assets/code/` | programmes de vérification |

## Reconstruire le site

Depuis la racine du dépôt :

```
python3 _sources/build.py
```

Pour produire une copie dans un autre dossier : `python3 _sources/build.py --diffusion DOSSIER`, puis copier `assets/` dans `DOSSIER`.

## Licence

- Texte, figures et exercices : [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.fr) (Creative Commons Attribution - Partage dans les mêmes conditions 4.0 International).
- Code (`assets/code/`, `assets/*.js`, `assets/style.css`, `_sources/build.py`) : licence MIT, voir [`LICENSE-CODE`](LICENSE-CODE).
- KaTeX (`assets/katex/`) garde sa propre licence MIT, voir `assets/katex/LICENSE`.

Le détail est dans [`LICENSE`](LICENSE).
