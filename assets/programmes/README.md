# Programmes du manuel « Calculabilité » (niveau technologique)

Ces programmes réalisent, jusqu’au dernier quadruplet, les constructions démontrées dans le manuel. Ils n’utilisent que Python 3 (version 3.8 ou plus récente), sans aucune bibliothèque à installer.

## Installation

Décompresser l’archive, ouvrir un terminal dans le dossier `programmes`, puis lancer :

```
python3 tests.py
```

Sous Windows, remplacer `python3` par `py` ou `python`. Le script vérifie toutes les affirmations en une dizaine de secondes et se termine par « Tout est conforme. »

## Les fichiers

| Fichier | Ce qu’il fait | Chapitre |
|---|---|---|
| `machines.py` | simulateur de machines de Turing à quadruplets ; lit les fichiers `.tm` | Machines de Turing |
| `exemples/*.tm` | les machines du chapitre 3 (addition, soustraction, multiplication, égalité…) | Machines de Turing |
| `recursives.py` | les fonctions récursives : termes C, S, A, σ, ρ, μ, évaluation, bibliothèque | Fonctions récursives |
| `compilateur.py` | compilateur fonctions récursives → machines de Turing | Équivalence |
| `turing_vers_recursif.py` | traduction machine de Turing → fonction récursive (forme normale de Kleene) | Équivalence |
| `lambda_calcul.py` | réducteur de λ-termes et compilateur fonctions récursives → λ-calcul | λ-calcul, Équivalence |
| `universelle.py` | fonction universelle U(e, x), puis machine de Turing universelle obtenue en la compilant | Universalité |
| `recursion.py` | théorème s-m-n sur les machines ; point fixe de Kleene ; quine | s-m-n et récursion |
| `arret.py` | l’argument diagonal exécuté contre plusieurs « décideurs » candidats | Indécidabilité |
| `piles.py` | automates à deux piles : traduction d’une machine de Turing, vérifiée pas à pas | Autres modèles |
| `compteurs.py` | la bande dans deux nombres, puis deux compteurs par les nombres premiers | Autres modèles |
| `post.py` | les dominos de Post d’une machine de Turing, et la solution tirée du calcul | Autres modèles |
| `logique_post.py` | des dominos à un énoncé logique avec une relation et une fonction binaires | Logique et types |
| `tests.py` | vérification de l’ensemble | |

## Exemples

```
python3 machines.py exemples/addition.tm 2 3 --trace
python3 recursives.py "rho[A(1,1), sigma[S, A(3,2)]]" 2 3
python3 compilateur.py mult 2 3 --sortie mult.tm
python3 machines.py mult.tm 2 3
python3 turing_vers_recursif.py exemples/soustraction_propre.tm 5 2
python3 lambda_calcul.py --compiler fact 3
python3 universelle.py
python3 universelle.py --machine
python3 recursion.py
python3 arret.py
python3 piles.py exemples/addition.tm 1 1 --trace
python3 compteurs.py exemples/addition.tm 2 1
python3 post.py
python3 logique_post.py
```

Chaque fichier commence par un commentaire qui explique ses conventions et son utilisation ; `python3 fichier.py` sans argument l’affiche.

## Licence

Licence MIT (voir `LICENSE-CODE` à la racine du manuel). Auteurs : Frédéric Prost et Claude.
