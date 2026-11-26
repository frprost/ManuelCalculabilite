#!/usr/bin/env python3
"""Vérifie tout ce que les programmes affirment.   python3 tests.py   (une dizaine de secondes)

Licence MIT. Frédéric Prost et Claude.
"""
import itertools
import os
import time

import recursives as r
from machines import Machine
from compilateur import compiler
import turing_vers_recursif as tvr
import universelle as uni
import lambda_calcul as lam
from recursion import smn, point_fixe, executer

ICI = os.path.dirname(os.path.abspath(__file__))
echecs = []


def verifier(nom, condition):
    if not condition:
        echecs.append(nom)
        print("  ÉCHEC :", nom)


def grille(k, n):
    return itertools.product(range(n), repeat=k)


def section(titre):
    print(titre)
    return time.time()


t = section("1. Bibliothèque : chaque version native coïncide avec son terme")
for nom, f in r.BIB.items():
    if f.natif is None:
        continue
    for a in grille(f.arite(), 5 if f.arite() < 3 else 4):
        verifier("%s%s" % (nom, a), r.evaluer(f, a) == r.evaluer(f, a, rapide=True))
print("   %d fonctions, %.1f s" % (sum(1 for f in r.BIB.values() if f.natif), time.time() - t))

t = section("2. Compilateur fonctions récursives -> machines de Turing")
for nom in ["add", "mult", "pred", "monus", "sg", "sgbar", "puiss", "fact", "eg", "inf", "div", "tri", "couple"]:
    f = r.BIB[nom]
    m = compiler(f)
    for a in grille(f.arite(), 4 if f.arite() == 1 else 3):
        if nom == "div" and a[1] == 0:
            continue
        verifier("compilé %s%s" % (nom, a), m.calculer(*a) == r.evaluer(f, a, rapide=True))
    print("   %-7s %6d quadruplets : conforme" % (nom, len(m)))
m = compiler(r.div)
try:
    m.executer(3, 0, max_pas=200000)
    verifier("div(3, 0) ne doit pas s'arrêter", False)
except Exception:
    pass
print("   div(3, 0) : la machine ne s'arrête pas (comme la fonction n'est pas définie)   %.1f s" % (time.time() - t))

t = section("3. Machines de Turing -> fonctions récursives (forme normale)")
for fichier, args in [("addition", [(0, 0), (2, 3), (1, 4)]), ("successeur", [(0,), (3,)]),
                      ("predecesseur", [(0,), (4,)]), ("soustraction_propre", [(2, 4), (5, 2)]),
                      ("projection_2_sur_3", [(1, 2, 3)]), ("signe", [(0,), (3,)])]:
    M = Machine.depuis_fichier(os.path.join(ICI, "exemples", fichier + ".tm"))
    for a in args:
        T, v, attendu = tvr.verifier(M, list(a))
        verifier("f_Z %s%s" % (fichier, a), v == attendu)
    print("   %-20s conforme pas à pas" % fichier)
print("   %.1f s" % (time.time() - t))

t = section("4. Fonction universelle U(code(Z), x)")
for nom, texte in uni.EXEMPLES.items():
    M = Machine.depuis_texte(texte)
    e = uni.code_machine(M)
    for x in range(4):
        verifier("U %s %d" % (nom, x), uni.U(e, x) == M.calculer(x))
M = Machine.depuis_fichier(os.path.join(ICI, "exemples", "test_nullite.tm"))
e = uni.code_machine(M)
for x in range(3):
    verifier("U test_nullite %d" % x, uni.U(e, x) == M.calculer(x))
print("   %d machines, %.1f s" % (len(uni.EXEMPLES) + 1, time.time() - t))

t = section("5. Compilateur fonctions récursives -> λ-calcul")
for nom, args in [("add", (2, 3)), ("mult", (2, 3)), ("pred", (3,)), ("monus", (5, 2)), ("eg", (2, 2)),
                  ("eg", (1, 2)), ("div", (7, 2)), ("fact", (3,))]:
    v, n = lam.calculer(r.BIB[nom], *args)
    verifier("λ %s%s" % (nom, args), v == r.evaluer(r.BIB[nom], args, rapide=True))
print("   conforme, %.1f s" % (time.time() - t))

t = section("6. s-m-n, quine, arrêt")
Z = compiler(r.mult)
for a in range(3):
    Za = smn(Z, a)
    verifier("smn mult %d" % a, [Za.calculer(y) for y in range(4)] == [a * y for y in range(4)])
q = point_fixe("print(MOI, end='')")
verifier("quine", executer(q) == q)
import arret
for nom, dec in arret.CANDIDATS.items():
    D = arret.paradoxe(dec)
    env = {}
    exec(D, env)
    rep = env["decide"](D, D)
    etat, _ = arret.lancer(D, D)
    verifier("arrêt " + nom, rep != (etat == "arrêt"))
print("   conforme, %.1f s" % (time.time() - t))

t = section("7. Deux piles, deux compteurs, dominos de Post, logique")
import glob
import piles
import compteurs
import post
import logique_post
ici = os.path.dirname(os.path.abspath(__file__))
for f in sorted(glob.glob(os.path.join(ici, "exemples", "*.tm"))):
    M = Machine.depuis_fichier(f)
    nom = os.path.basename(f)[:-3]
    for a in [(0,), (2,), (1, 1), (2, 1)]:
        try:
            M.executer(*a, max_pas=3000)
        except Exception:
            continue
        piles.comparer(M, *a)
        compteurs.comparer(M, *a, deux=(nom != "multiplication"))
        d, noms = post.dominos_modifies(M, *a)
        s = post.solution_depuis_calcul(M, d, noms, *a)
        verifier("post modifié %s %s" % (nom, a), post.est_solution(d, s, premier=0))
        verifier("post %s %s" % (nom, a), post.est_solution(post.vers_ordinaire(d), post.solution_ordinaire(s, len(d))))
D3 = [(("a",), ("b", "a", "a")), (("a", "b"), ("a", "a")), (("b", "b", "a"), ("b", "b"))]
sol = post.chercher(D3)
verifier("recherche de Post", post.est_solution(D3, sol))
f = logique_post.deduction(D3, sol)
verifier("déduction de Floyd", f[-1][0] == f[-1][1])
verifier("modèle des mots", post.est_solution(D3, logique_post.modele_des_mots(D3, 8)))
print("   11 machines, %.1f s" % (time.time() - t))

print()
print("Tout est conforme." if not echecs else "%d échecs." % len(echecs))
raise SystemExit(1 if echecs else 0)
