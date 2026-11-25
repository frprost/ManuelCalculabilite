"""Un solveur SAT moderne face à trois familles de formules (chapitre « Complexité »).

Nécessite le paquet python-sat (pip install python-sat), qui fournit le solveur CaDiCaL.
1. Formules structurées (n reines) : des dizaines de milliers de variables, résolues vite.
2. 3-SAT aléatoire au seuil (4,26 clauses par variable) : le temps croît vite avec n.
3. Principe des tiroirs (n+1 pigeons, n trous) : insatisfaisable, et exponentiel pour
   tout solveur fondé sur la résolution (Haken, 1985).
"""
import random, statistics, time
from itertools import combinations
from pysat.solvers import Solver

SOLVEUR = "cd15"   # CaDiCaL 1.5


def resoudre(clauses):
    t0 = time.perf_counter()
    with Solver(name=SOLVEUR, bootstrap_with=clauses) as s:
        rep = s.solve()
        conflits = s.accum_stats().get("conflicts", 0)
    return rep, time.perf_counter() - t0, conflits


def reines(n):
    v = lambda i, j: i * n + j + 1
    C = [[v(i, j) for j in range(n)] for i in range(n)]                 # une reine par ligne
    for i in range(n):
        for j1, j2 in combinations(range(n), 2):
            C.append([-v(i, j1), -v(i, j2)])                            # pas deux par ligne
            C.append([-v(j1, i), -v(j2, i)])                            # pas deux par colonne
    for d in range(-n + 1, 2 * n):                                      # diagonales
        for diag in ([(i, i - d) for i in range(n) if 0 <= i - d < n],
                     [(i, d - i) for i in range(n) if 0 <= d - i < n]):
            for a, b in combinations(diag, 2):
                C.append([-v(*a), -v(*b)])
    return C, n * n


def aleatoire_3sat(n, ratio, graine):
    r = random.Random(graine)
    return [[x * r.choice((1, -1)) for x in r.sample(range(1, n + 1), 3)] for _ in range(round(ratio * n))]


def pigeons(n):                                   # n+1 pigeons, n trous
    v = lambda p, h: p * n + h + 1
    C = [[v(p, h) for h in range(n)] for p in range(n + 1)]
    for h in range(n):
        for p1, p2 in combinations(range(n + 1), 2):
            C.append([-v(p1, h), -v(p2, h)])
    return C, (n + 1) * n


if __name__ == "__main__":
    import sys
    parties = sys.argv[1:] or ["1", "2", "3"]
    if "1" in parties:
        print("1. n reines")
        for n in (30, 60, 100):
            C, nv = reines(n)
            rep, t, c = resoudre(C)
            print(f"   n={n:3d} : {nv:6d} variables, {len(C):8d} clauses -> {'SAT' if rep else 'UNSAT'} en {t:.2f} s", flush=True)
    if "2" in parties:
        print("2. 3-SAT aléatoire, 4,26 clauses par variable (médiane sur 5 formules)")
        for n in (100, 150, 200, 250, 300):
            res = [resoudre(aleatoire_3sat(n, 4.26, g)) for g in range(5)]
            print(f"   n={n:3d} : temps médian {statistics.median(r[1] for r in res):8.3f} s, "
                  f"conflits médians {int(statistics.median(r[2] for r in res)):9d}", flush=True)
    if "3" in parties:
        print("3. principe des tiroirs")
        for n in range(7, 11):
            C, nv = pigeons(n)
            rep, t, c = resoudre(C)
            print(f"   {n+1:2d} pigeons, {n:2d} trous : {nv:4d} variables -> {'SAT' if rep else 'UNSAT'} en {t:8.2f} s, {c} conflits", flush=True)
