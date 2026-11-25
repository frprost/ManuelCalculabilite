"""Expériences du chapitre « Hasard, approximation et calcul quantique ».

1. Test de Miller-Rabin : nombre de « menteurs forts » pour chaque composé impair < 5000.
2. Lemme de Schwartz-Zippel : tester une identité polynomiale en un point aléatoire.
3. MAX-3SAT : une valuation au hasard satisfait en moyenne 7/8 des clauses.
4. Algorithme de Deutsch, Grover et Shor, simulés exactement sur un vecteur d'état.
Aucune bibliothèque extérieure : les nombres complexes de Python suffisent.
"""
import cmath
import math
import random
from fractions import Fraction


# 1. Miller-Rabin ---------------------------------------------------------------
def temoin(a, n):
    """True si a prouve que n (impair > 2) est composé."""
    d, s = n - 1, 0
    while d % 2 == 0:
        d, s = d // 2, s + 1
    x = pow(a, d, n)
    if x in (1, n - 1):
        return False
    for _ in range(s - 1):
        x = x * x % n
        if x == n - 1:
            return False
    return True


def miller_rabin(n, k=20):
    if n < 4:
        return n in (2, 3)
    if n % 2 == 0:
        return False
    return not any(temoin(random.randrange(2, n - 1), n) for _ in range(k))


def premier(n):
    return n > 1 and all(n % p for p in range(2, math.isqrt(n) + 1))


# 2. Schwartz-Zippel --------------------------------------------------------------
def identite_probable(P, Q, nvars, degre, essais=20, S=10**6):
    """Teste P = Q (polynômes donnés comme fonctions) en des points aléatoires de {0..S-1}^n.
    Si P != Q, chaque essai se trompe avec probabilité au plus degre/S."""
    for _ in range(essais):
        x = [random.randrange(S) for _ in range(nvars)]
        if P(*x) != Q(*x):
            return False
    return True


# 3. MAX-3SAT -----------------------------------------------------------------------
def formule_aleatoire(n, m):
    return [[random.choice([1, -1]) * v for v in random.sample(range(1, n + 1), 3)] for _ in range(m)]


def fraction_satisfaite(F, val):
    return sum(any((l > 0) == val[abs(l)] for l in c) for c in F) / len(F)


# 4. Simulation quantique : un état est la liste des 2^n amplitudes ------------------
def hadamard(etat, q):
    r = 1 / math.sqrt(2)
    nouv = etat[:]
    for i in range(len(etat)):
        if not (i >> q) & 1:
            a, b = etat[i], etat[i | 1 << q]
            nouv[i], nouv[i | 1 << q] = r * (a + b), r * (a - b)
    return nouv


def deutsch(f):
    """Un seul appel à l'oracle U_f |x, y> = |x, y xor f(x)> : décide si f(0) = f(1).
    Qubit 0 : x ; qubit 1 : y."""
    etat = [0j] * 4
    etat[0b10] = 1                                  # x = 0, y = 1
    etat = hadamard(hadamard(etat, 0), 1)
    nouv = [0j] * 4
    for i, a in enumerate(etat):                    # l'unique appel à l'oracle
        x, y = i & 1, i >> 1
        nouv[x | (y ^ f(x)) << 1] += a
    etat = hadamard(nouv, 0)
    p1 = sum(abs(a) ** 2 for i, a in enumerate(etat) if i & 1)
    return "constante" if p1 < 1e-9 else "équilibrée"


def grover(n, cible):
    N = 2 ** n
    etat = [1 / math.sqrt(N)] * N
    k = int(math.pi / 4 * math.sqrt(N))
    for _ in range(k):
        etat[cible] = -etat[cible]                  # oracle : change le signe de la cible
        m = sum(etat) / N
        etat = [2 * m - a for a in etat]            # inversion autour de la moyenne
    return k, abs(etat[cible]) ** 2


def shor_simule(N, a, t=8):
    """Recherche de période de x -> a^x mod N avec un registre de t qubits (Q = 2^t).
    On calcule exactement la loi de la mesure après la transformée de Fourier."""
    Q = 2 ** t
    valeurs = {}
    for x in range(Q):
        valeurs.setdefault(pow(a, x, N), []).append(x)
    loi = [0.0] * Q
    for xs in valeurs.values():                     # chaque résultat possible de la mesure de f(x)
        # état après mesure : somme des |x>, x dans xs, normalisée ; après Fourier, l'amplitude de |y>
        # est somme exp(2iπxy/Q) / sqrt(Q·|xs|) ; on pondère par la probabilité |xs|/Q de ce résultat
        for y in range(Q):
            s = sum(cmath.exp(2j * math.pi * x * y / Q) for x in xs)
            loi[y] += abs(s) ** 2 / Q ** 2
    return loi


def periode_depuis_mesure(y, Q, N):
    """Fractions continues : le dénominateur de la meilleure approximation de y/Q."""
    return Fraction(y, Q).limit_denominator(N).denominator


def facteurs_depuis_periode(N, a, r):
    if r % 2 or pow(a, r // 2, N) == N - 1:
        return None
    return math.gcd(pow(a, r // 2) - 1, N), math.gcd(pow(a, r // 2) + 1, N)


if __name__ == "__main__":
    random.seed(0)
    pire = max(((sum(not temoin(a, n) for a in range(2, n - 1)) / (n - 3), n)
                for n in range(9, 5000, 2) if not premier(n)))
    print("1. Miller-Rabin : pire proportion de menteurs forts pour n < 5000 impair composé :",
          f"{pire[0]:.4f} (n = {pire[1]}), borne théorique 1/4")
    print("   561 = 3·11·17 (nombre de Carmichael) : 2^560 mod 561 =", pow(2, 560, 561),
          "; témoin de Miller-Rabin pour a = 2 :", temoin(2, 561))
    print("   erreurs sur les n < 20000 avec 20 essais :",
          sum(miller_rabin(n) != premier(n) for n in range(2, 20000)))
    vrai = identite_probable(lambda x, y: (x + y) ** 5,
                             lambda x, y: x**5 + 5*x**4*y + 10*x**3*y**2 + 10*x**2*y**3 + 5*x*y**4 + y**5, 2, 5)
    faux = identite_probable(lambda x, y: (x + y) ** 5,
                             lambda x, y: x**5 + 5*x**4*y + 10*x**3*y**2 + 10*x**2*y**3 + 4*x*y**4 + y**5, 2, 5)
    print("2. Schwartz-Zippel : (x+y)^5 = développement exact :", vrai, "; avec une faute :", faux)
    F = formule_aleatoire(100, 2000)
    fr = [fraction_satisfaite(F, {v: random.random() < .5 for v in range(1, 101)}) for _ in range(200)]
    print("3. MAX-3SAT : moyenne sur 200 valuations au hasard :", round(sum(fr) / len(fr), 4), "(7/8 = 0,875)")
    print("4. Deutsch :", [deutsch(f) for f in (lambda x: 0, lambda x: 1, lambda x: x, lambda x: 1 - x)])
    for n in (4, 8, 12):
        k, p = grover(n, 5)
        print(f"   Grover, N = 2^{n} = {2**n} : {k} appels à l'oracle, probabilité de trouver la cible {p:.4f}")
    for N, a in ((15, 7), (21, 2)):
        t = (N * N - 1).bit_length()                # 2^t >= N^2, comme dans l'algorithme de Shor
        Q = 2 ** t
        loi = shor_simule(N, a, t)
        pics = [y for y in range(Q) if loi[y] > 0.02]
        # chaque mesure y donne un dénominateur d (un diviseur de r, souvent r lui-même) ;
        # on essaie ses petits multiples, ce qui est un calcul classique facile
        candidats = []
        for y in pics:
            d = periode_depuis_mesure(y, Q, N)
            candidats += [d * k for k in range(1, N // d + 1) if pow(a, d * k, N) == 1][:1]
        r = min(candidats)
        print(f"   Shor, N = {N}, a = {a}, Q = 2^{t} : mesures probables {pics}",
              f"(probabilité totale {sum(loi[y] for y in pics):.3f} ; loi totale {sum(loi):.3f}), période r = {r},",
              "facteurs", facteurs_depuis_periode(N, a, r))
