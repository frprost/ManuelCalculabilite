#!/usr/bin/env python3
"""Théorème s-m-n et théorème de récursion, réalisés (chapitre « s-m-n et récursion » du manuel).

1. s-m-n sur les machines de Turing. À partir d'une machine Z qui calcule f(a, y) et d'un entier a,
   smn(Z, a) fabrique une machine qui calcule y -> f(a, y) : elle écrit le bloc de a devant
   son entrée, revient sur sa première barre, puis exécute Z. La fabrication est elle-même
   un calcul (une fonction de a), ce qui est tout le contenu du théorème.

2. Point fixe (théorème de récursion de Kleene) sur des programmes Python. point_fixe(corps)
   renvoie le texte d'un programme qui dispose, dans la variable MOI, de son propre texte
   complet, puis exécute corps. Avec corps = "print(MOI, end='')" on obtient un programme qui
   affiche son propre texte (une « quine »). La construction est celle de la preuve : un
   gabarit appliqué à sa propre description, comme s(e, e) dans la démonstration.

    python3 recursion.py                 démonstrations
    python3 recursion.py --quine         affiche une quine (à enregistrer et exécuter)

Licence MIT. Frédéric Prost et Claude.
"""
import io
import contextlib
import sys

from machines import Machine, BLANC as B, BARRE as I


# ------------------------------------------------------------------ s-m-n
def smn(machine, a):
    """Machine qui, sur l'entrée y, calcule ce que `machine` calcule sur (a, y)."""
    ren = {q: "z_" + q for q in machine.etats()}
    quads = []
    # depuis la première barre de y : reculer sur le séparateur, puis encore d'une case
    quads.append(("q0", I, "L", "w0"))
    quads.append(("w0", B, "L", "w1"))
    # écrire a+1 barres vers la gauche
    for t in range(1, a + 2):
        quads.append(("w%d" % t, B, I, "v%d" % t))
        quads.append(("v%d" % t, I, "L", "w%d" % (t + 1)))
    # une case trop loin : revenir sur la première barre du bloc de a, et lancer la machine
    quads.append(("w%d" % (a + 2), B, "R", ren[machine.etat_initial]))
    quads += [(ren[q], s, act, ren[q2]) for q, s, act, q2 in machine.quadruplets]
    return Machine(quads, "q0")


# ------------------------------------------------------------------ point fixe
MARQUE = "@" + "@"


def point_fixe(corps):
    """Texte P d'un programme Python qui, exécuté, place son propre texte dans MOI puis exécute corps.

    Gabarit T = « _T = @@ ; MOI = _T.replace(marque, repr(_T)) ; corps ».
    P = T où @@ est remplacé par repr(T). À l'exécution, _T vaut T, donc MOI vaut P."""
    if MARQUE in corps:
        raise ValueError("le corps ne doit pas contenir la marque")
    gabarit = "_T = %s\nMOI = _T.replace('@' + '@', repr(_T))\n%s\n" % (MARQUE, corps)
    return gabarit.replace(MARQUE, repr(gabarit))


def executer(source, **variables):
    """Exécute un texte de programme et renvoie ce qu'il affiche."""
    sortie = io.StringIO()
    with contextlib.redirect_stdout(sortie):
        exec(source, dict(variables))
    return sortie.getvalue()


def _demonstration():
    from compilateur import compiler
    from recursives import add, mult
    print("1. s-m-n sur les machines de Turing")
    for f, nom in ((add, "add"), (mult, "mult")):
        Z = compiler(f)
        for a in (0, 2, 3):
            Za = smn(Z, a)
            vals = [Za.calculer(y) for y in range(4)]
            attendu = [f(a, y) for y in range(4)]
            assert vals == attendu
            print("   %s(%d, y) pour y = 0..3 : %s   (machine de %d quadruplets, %d de plus que Z)"
                  % (nom, a, vals, len(Za), len(Za) - len(Z)))
    print()
    print("2. Une quine : un programme qui affiche son propre texte")
    q = point_fixe("print(MOI, end='')")
    print("   " + q.replace("\n", "\n   "))
    assert executer(q) == q
    print("   vérifié : sa sortie est exactement son texte.")
    print()
    print("3. Un programme qui utilise son propre texte : il affiche sa longueur et son nombre de lignes")
    p = point_fixe("print(len(MOI), MOI.count(chr(10)))")
    print("   sortie :", executer(p).strip(), "  longueur réelle :", len(p), p.count("\n"))


if __name__ == "__main__":
    if "--quine" in sys.argv:
        print(point_fixe("print(MOI, end='')"), end="")
    else:
        _demonstration()
