"""Complexité : deux expériences (chapitre « Complexité »).

1. Accessibilité dans un graphe : parcours en largeur (mémoire proportionnelle au
   nombre de sommets) contre l'algorithme récursif de Savitch (profondeur de pile
   log2 N, chaque niveau ne retenant que trois sommets), au prix d'un temps énorme.
2. Le codage de Cook et Levin pour une petite machine non déterministe, vérifié
   par un petit solveur SAT (recherche avec propagation unitaire).
"""
from itertools import product
from math import ceil, log2


# ---------- 1. Savitch ----------
def accessible_largeur(arcs, n, s, t):
    vus, file = {s}, [s]
    while file:
        u = file.pop(0)
        for v in range(n):
            if (u, v) in arcs and v not in vus:
                vus.add(v)
                file.append(v)
    return t in vus, len(vus)               # mémoire : jusqu'à n sommets retenus


def savitch(arcs, n, s, t):
    stats = {"appels": 0, "profondeur": 0}

    def acces(u, v, i, prof):                # v accessible depuis u en au plus 2^i arcs ?
        stats["appels"] += 1
        stats["profondeur"] = max(stats["profondeur"], prof)
        if i == 0:
            return u == v or (u, v) in arcs
        return any(acces(u, m, i - 1, prof + 1) and acces(m, v, i - 1, prof + 1) for m in range(n))

    return acces(s, t, ceil(log2(n)), 0), stats


# ---------- 2. Cook-Levin ----------
# Machine à une bande, non déterministe : sur une entrée de 0 et de 1, elle « devine »
# une case contenant 1 en avançant vers la droite, et accepte si elle en trouve une.
# Transitions (état, lu) -> ensemble de (état, écrit, déplacement).
DELTA = {
    ("q", "0"): {("q", "0", 1)},
    ("q", "1"): {("q", "1", 1), ("acc", "1", 0)},
    ("acc", "0"): {("acc", "0", 0)}, ("acc", "1"): {("acc", "1", 0)}, ("acc", "B"): {("acc", "B", 0)},
}
ETATS, SYMB = ("q", "acc"), ("0", "1", "B")


def formule_cook_levin(entree, p):
    """Clauses (en forme normale conjonctive) du tableau de Cook-Levin, pour p pas et les cases 0..p."""
    var = {}
    def v(*cle):                              # numéro de variable
        return var.setdefault(cle, len(var) + 1)
    C, cases, T = [], range(p + 1), range(p + 1)
    def exactement_un(lits):
        C.append(list(lits))
        C.extend([[-a, -b] for k, a in enumerate(lits) for b in lits[k + 1:]])
    for i in T:                               # chaque ligne : un état, une position, un symbole par case
        exactement_un([v("Q", i, s) for s in ETATS])
        exactement_un([v("H", i, j) for j in cases])
        for j in cases:
            exactement_un([v("X", i, j, a) for a in SYMB])
    C.append([v("Q", 0, "q")]); C.append([v("H", 0, 0)])           # ligne initiale
    for j in cases:
        C.append([v("X", 0, j, entree[j] if j < len(entree) else "B")])
    for i in range(p):                        # transitions
        for j in cases:
            for a in SYMB:                    # case loin de la tête : inchangée
                C.append([v("H", i, j), -v("X", i, j, a), v("X", i + 1, j, a)])
            for s in ETATS:
                for a in SYMB:
                    choix = [(s2, b, d) for (s2, b, d) in DELTA.get((s, a), ()) if 0 <= j + d <= p]
                    hyp = [-v("H", i, j), -v("Q", i, s), -v("X", i, j, a)]
                    # au moins un choix : on introduit une variable par choix
                    cs = [v("C", i, j, s, a, k) for k in range(len(choix))]
                    C.append(hyp + cs)
                    for c, (s2, b, d) in zip(cs, choix):
                        for lit in (v("Q", i + 1, s2), v("X", i + 1, j, b), v("H", i + 1, j + d)):
                            C.append(hyp + [-c, lit])
    C.append([v("Q", p, "acc")])              # acceptation
    return C, len(var)


def dpll(clauses, affect=None):
    """Recherche exhaustive avec propagation unitaire."""
    affect = dict(affect or {})
    while True:
        reste, unit = [], None
        for c in clauses:
            if any(affect.get(abs(l)) == (l > 0) for l in c):
                continue
            libres = [l for l in c if abs(l) not in affect]
            if not libres:
                return None
            if len(libres) == 1:
                unit = libres[0]
            reste.append(libres)
        if not reste:
            return affect
        if unit is None:
            break
        affect[abs(unit)] = unit > 0
    l = reste[0][0]
    for val in (l > 0, l <= 0):
        r = dpll(reste, {**affect, abs(l): val})
        if r is not None:
            return r
    return None


def accepte_par_formule(entree, p):
    clauses, _ = formule_cook_levin(entree, p)
    return dpll(clauses) is not None


def accepte_directement(entree):
    return "1" in entree


if __name__ == "__main__":
    n = 64
    arcs = {(i, i + 1) for i in range(n - 1)} | {(i, i + 2) for i in range(0, n - 2, 7)}
    print("1. largeur :", accessible_largeur(arcs, n, 0, n - 1))
    rep, st = savitch(arcs, 16, 0, 15)
    print("   Savitch sur 16 sommets : accessible =", rep, "; appels =", st["appels"],
          "; profondeur de pile =", st["profondeur"], "(log2 16 = 4)")
    cl, nv = formule_cook_levin("0010", 5)
    print("2. formule pour l'entrée 0010 et 5 pas :", nv, "variables,", len(cl), "clauses")
    ok = all(accepte_par_formule("".join(w), len(w) + 1) == accepte_directement("".join(w))
             for k in range(0, 7) for w in product("01", repeat=k))
    print("   satisfaisabilité de la formule : accord avec la machine sur les 127 mots de longueur <= 6 :", ok)
