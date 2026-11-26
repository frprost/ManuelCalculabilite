#!/usr/bin/env python3
"""Une fonction universelle, puis une machine de Turing universelle, construites de bout en bout.

1. On code toute machine Z par un entier code(Z) (couples de Cantor, voir plus bas).
2. On écrit UN terme récursif U(e, x), fait des seules briques C, S, A, sigma, rho, mu,
   tel que U(code(Z), x) = Psi_Z(x) pour toute machine Z (même domaine de définition).
   C'est la même construction que dans turing_vers_recursif.py, mais la machine n'est plus
   fixée : sa table de quadruplets est lue dans l'argument e. Le chapitre « Universalité » du
   manuel en donne la démonstration ; ce fichier en est la réalisation.
3. On compile U avec compilateur.py : on obtient une machine de Turing universelle U_TM,
   telle que U_TM, lancée sur (code(Z), x), calcule Psi_Z(x).

Codage d'une machine à b symboles (0 = B, 1 = barre, 2, ...) et k états (0 = q0, 1, ...) :
  action        : 0 = L, 1 = R, 2 + j = écrire le symbole j
  table         : un entier écrit en base N = (b+2)·k + 1 ; son chiffre de rang i·b + s vaut
                  0 si aucun quadruplet ne commence par (q_i, s), et action·k + i2 + 1 pour (q_i, s, action, q_i2)
  machine       : <b, <k, table>>
(Un codage par listes de couples de Cantor imbriqués conviendrait aussi en théorie, mais ses
nombres doublent de longueur à chaque quadruplet : 3 millions de chiffres binaires pour 16
quadruplets. La table en base N a une longueur proportionnelle au nombre de quadruplets.)

Utilisation :
    python3 universelle.py                      démonstration : U simule plusieurs machines
    python3 universelle.py --machine            compile U en machine de Turing (environ 1 min 30) et donne sa taille
    python3 universelle.py --machine --ecrire   ... et l'écrit dans universelle.tm (environ 680 Mo)
    python3 universelle.py fichier.tm 3         code(Z) puis U(code(Z), 3)

Licence MIT. Frédéric Prost et Claude.
"""
import sys

import recursives as r
from recursives import App, fonction, recurrence, minimisation
from machines import Machine, BLANC, BARRE
from turing_vers_recursif import cases

G, D = r.gauche, r.droite


def conf(g, i, d):
    return App(r.couple, g, App(r.couple, i, d))


# --- lecture du code de la machine : e = <b, <k, table>>
nb_symboles = fonction(1, lambda e: App(G, e), "nb_symboles")
nb_etats = fonction(1, lambda e: App(G, App(D, e)), "nb_etats")
table = fonction(1, lambda e: App(D, App(D, e)), "table")
# base de la table : N = (b + 2)·k + 1 (une entrée vaut 0, ou action·k + i2 + 1)
base = fonction(1, lambda e: App(r.add, App(r.mult, App(r.add, App(nb_symboles, e), 2), App(nb_etats, e)), 1), "base")
# configuration <g, <i, d>>
cg = fonction(1, lambda c: App(G, c), "cg")
ci = fonction(1, lambda c: App(G, App(D, c)), "ci")
cd = fonction(1, lambda c: App(D, App(D, c)), "cd")
lu = fonction(2, lambda e, c: App(r.reste, App(cd, c), App(nb_symboles, e)), "lu")

# --- l'entrée de la table pour (état i, symbole s) : le chiffre de rang i·b + s de la table, en base N.
chercher = fonction(3, lambda e, i, s: App(r.reste,
                                          App(r.quot, App(table, e),
                                              App(r.puiss, App(base, e), App(r.add, App(r.mult, i, App(nb_symboles, e)), s))),
                                          App(base, e)), "chercher")


def _etape(e, c):
    b = App(nb_symboles, e)
    res = App(chercher, e, App(ci, c), App(lu, e, c))
    act = App(r.quot, App(r.pred, res), App(nb_etats, e))
    i2 = App(r.reste, App(r.pred, res), App(nb_etats, e))
    g, d, s = App(cg, c), App(cd, c), App(lu, e, c)
    gauche_ = conf(App(r.quot, g, b), i2, App(r.add, App(r.mult, d, b), App(r.reste, g, b)))
    droite_ = conf(App(r.add, App(r.mult, g, b), s), i2, App(r.quot, d, b))
    ecrire = conf(g, i2, App(r.add, App(r.monus, d, s), App(r.monus, act, 2)))
    trouve = App(r.sg, res)
    return cases([(App(r.et, trouve, App(r.eg, act, 0)), gauche_),
                  (App(r.et, trouve, App(r.eg, act, 1)), droite_),
                  (App(r.et, trouve, App(r.inf, 1, act)), ecrire)], c)


etapeU = fonction(2, _etape, "etapeU")
arretU = fonction(2, lambda e, c: App(r.sgbar, App(chercher, e, App(ci, c), App(lu, e, c))), "arretU")
iterU = recurrence(3, lambda e, c: c, lambda t, acc, e, c: App(etapeU, e, acc), "iterU")
# rep(x, b) = 1 + b + ... + b^x : la bande 1^{x+1}
repU = recurrence(2, lambda b: 1, lambda y, acc, b: App(r.add, App(r.mult, acc, b), 1), "repU")
initU = fonction(2, lambda e, x: conf(0, 0, App(repU, x, App(nb_symboles, e))), "initU")
compteU = recurrence(3, lambda m, b: App(r.couple, m, 0),
                     lambda k, p, m, b: App(r.couple, App(r.quot, App(G, p), b),
                                            App(r.add, App(D, p), App(r.eg, App(r.reste, App(G, p), b), 1))),
                     "compteU")
barresU = fonction(4, lambda e, t, c, x: App(r.add,
                                             App(D, App(compteU, App(r.add, t, App(r.add, x, 2)), App(cg, c), App(nb_symboles, e))),
                                             App(D, App(compteU, App(r.add, t, App(r.add, x, 2)), App(cd, c), App(nb_symboles, e)))),
                   "barresU")
tempsU = minimisation(2, lambda e, x, t: App(r.non, App(arretU, e, App(iterU, t, e, App(initU, e, x)))), "tempsU")
U = fonction(2, lambda e, x: App(barresU, e, App(tempsU, e, x), App(iterU, App(tempsU, e, x), e, App(initU, e, x)), x), "U")


def code_machine(m):
    """L'entier code(Z) = <b, <k, table>> d'une machine du simulateur."""
    syms = [BLANC, BARRE] + sorted(m.symboles() - {BLANC, BARRE})
    etats = [m.etat_initial] + sorted(m.etats() - {m.etat_initial})
    ns = {s: k for k, s in enumerate(syms)}
    ne = {q: k for k, q in enumerate(etats)}
    b, k = len(syms), len(etats)
    N = (b + 2) * k + 1
    tab = 0
    for q, s, a, q2 in m.quadruplets:
        act = 0 if a == "L" else 1 if a == "R" else 2 + ns[a]
        tab += (act * k + ne[q2] + 1) * N ** (ne[q] * b + ns[s])
    return r.cantor(b, r.cantor(k, tab))


EXEMPLES = {
    "identité (efface une barre)": "q0 1 B q1",
    "successeur": "q0 B B q0",
    "aller-retour (identité, 7 quadruplets)": "q0 1 R q0\nq0 B 1 q1\nq1 1 L q1\nq1 B R q2\nq2 1 B q3\nq3 B R q4\nq4 1 B q5",
    "prédécesseur": "q0 1 B q1\nq1 B R q2\nq2 1 B q3",
}


def _principal(argv):
    if len(argv) >= 2 and argv[1] == "--machine":
        from compilateur import compiler
        print("terme U : %d briques une fois déplié, une seule minimisation non bornée" % r.taille(U))
        m = compiler(U)
        print("machine universelle : %d quadruplets, %d états, symboles B, 1, X" % (len(m), len(m.etats())))
        if "--ecrire" in argv:   # environ 680 Mo
            with open("universelle.tm", "w", encoding="utf-8") as f:
                f.write("# Machine de Turing universelle obtenue en compilant le terme U de universelle.py\n")
                f.write("# Entrée : code(Z), x  (deux blocs de barres).  Sortie : Psi_Z(x) barres.\n")
                f.write(m.en_texte())
            print("écrite dans universelle.tm")
        else:
            print("(ajouter --ecrire pour l'écrire dans universelle.tm : environ 680 Mo)")
        return 0
    if len(argv) >= 3:
        m = Machine.depuis_fichier(argv[1])
        x = int(argv[2])
        e = code_machine(m)
        print("code(Z) =", e)
        print("U(code(Z), %d) = %d   (la machine donne %d)" % (x, U(e, x), m.calculer(x)))
        return 0
    print("terme U : %d briques une fois déplié\n" % r.taille(U))
    for nom, texte in EXEMPLES.items():
        m = Machine.depuis_texte(texte)
        e = code_machine(m)
        for x in range(4):
            v = U(e, x)
            assert v == m.calculer(x), (nom, x)
        print("%-30s code = %s..." % (nom, str(e)[:40]))
        print("%-30s U(code, x) pour x = 0..3 : %s" % ("", [U(e, x) for x in range(4)]))
    return 0


if __name__ == "__main__":
    sys.exit(_principal(sys.argv))
