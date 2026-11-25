"""Trois réductions du chapitre « L'indécidable en mathématiques ordinaires ».

1. Un programme FRACTRAN devient une fonction de Collatz généralisée (Conway, 1972).
2. Une instance du problème de Post devient un ensemble de matrices 3x3 entières.
3. Une machine de Turing devient un jeu de tuiles de Wang avec tuile d'origine.
"""
from fractions import Fraction
from math import lcm
from itertools import product as prod


# 1. FRACTRAN -> Collatz généralisée -------------------------------------------
def collatz_de_fractran(fracs):
    """Renvoie (M, coef) : g(n) = coef(n % M) * n, où coef(r) = 1 si aucune fraction ne
    s'applique (point fixe). Le choix de la fraction ne dépend que de n mod M. La table
    des M valeurs de coef est finie ; on la calcule à la demande, car M peut être grand."""
    M = lcm(*(f.denominator for f in fracs))

    def coef(r):
        for f in fracs:
            if r % f.denominator == 0:     # f.den divise n  <=>  f.den divise n mod M (car f.den | M)
                return f
        return Fraction(1)
    return M, coef


def fractran(fracs, n, pas_max=10**6):
    for _ in range(pas_max):
        for f in fracs:
            if (n * f).denominator == 1:
                n = int(n * f)
                break
        else:
            return n
    return None


def iterer_collatz(M, table, n, pas_max=10**6):
    for _ in range(pas_max):
        m = int(table(n % M) * n)
        if m == n:
            return n
        n = m
    return None


# 2. Problème de Post -> matrices -------------------------------------------------
def sigma(w):                       # mot sur {a,b} -> entier en base 3, chiffres 1 et 2
    v = 0
    for c in w:
        v = 3 * v + (1 if c == 'a' else 2)
    return v


def matrice(u, v):
    return [[3 ** len(u), 0, sigma(u)], [0, 3 ** len(v), sigma(v)], [0, 0, 1]]


def mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


# 3. Machine de Turing -> tuiles de Wang ------------------------------------------
def tuiles(delta, q0, blanc='0'):
    """delta[(q, s)] = (q2, s2, 'G' ou 'D'). Tuile = (bas, haut, gauche, droite).
    Une ligne = un instant ; la couleur verticale est le contenu de la case
    (symbole, ou couple (état, symbole) sous la tête). Les symboles de la case 0 sont
    marqués (suffixe ^) et ses tuiles ont la couleur gauche '|' : aucune tête ne peut
    surgir du bord gauche."""
    symboles = {s for (_, s) in delta} | {s2 for (_, s2, _) in delta.values()} | {blanc}
    etats = {q for (q, _) in delta} | {q2 for (q2, _, _) in delta.values()}
    T = set()
    for s in symboles:
        m = s + '^'
        T.add((s, s, '-', '-'))                          # case loin de la tête
        T.add((m, m, '|', '-'))
        for q in etats:
            T.add((s, (q, s), q + '>', '-'))             # la tête arrive par la gauche
            T.add((s, (q, s), '-', '<' + q))             # la tête arrive par la droite
            T.add((m, (q, m), '|', '<' + q))
    for (q, s), (q2, s2, d) in delta.items():
        if d == 'D':
            T.add(((q, s), s2, '-', q2 + '>'))
            T.add(((q, s + '^'), s2 + '^', '|', q2 + '>'))
        else:
            T.add(((q, s), s2, '<' + q2, '-'))           # en case 0 : pas de tuile (sortie à gauche)
    origine = ('*', (q0, blanc + '^'), '|', 'i')          # ligne 0 : la configuration initiale
    T.add(origine)
    T.add(('*', blanc, 'i', 'i'))
    return T, origine


def pave_carre(T, origine, n):
    """Cherche (par retour arrière, sans connaître la machine) un pavage du carré n x n
    avec la tuile d'origine en bas à gauche. Les bords sont libres : aucune contrainte hors du carré."""
    grille = {}
    cases = [(x, y) for y in range(n) for x in range(n)]

    def ok(t, x, y):
        if (x, y) == (0, 0):
            return t == origine
        if y == 0 and t[0] != '*':
            return False
        if y > 0 and grille[x, y - 1][1] != t[0]:
            return False
        if x > 0 and grille[x - 1, y][3] != t[2]:
            return False
        return True

    def essayer(i):
        if i == len(cases):
            return True
        x, y = cases[i]
        for t in T:
            if ok(t, x, y):
                grille[x, y] = t
                if essayer(i + 1):
                    return True
        return False
    return essayer(0)


if __name__ == "__main__":
    # 1. l'addition en FRACTRAN : 2^a 3^b -> 3^(a+b)
    add = [Fraction(3, 2)]
    M, table = collatz_de_fractran(add)
    print("1. FRACTRAN [3/2] : g(n) =", ", ".join(f"{table(r)}·n si n ≡ {r} mod {M}" for r in range(M)))
    ok = all(fractran(add, 2**a * 3**b) == iterer_collatz(M, table, 2**a * 3**b) == 3**(a + b)
             for a in range(6) for b in range(6))
    prime = [Fraction(*p) for p in [(17, 91), (78, 85), (19, 51), (23, 38), (29, 33), (77, 29), (95, 23),
             (77, 19), (1, 17), (11, 13), (13, 11), (15, 14), (15, 2), (55, 1)]]
    M2, t2 = collatz_de_fractran(prime)
    n, a, b, puiss = 2, 2, 2, []
    for _ in range(20000):            # PRIMEGAME, par la fonction de Collatz associée
        n = int(t2(n % M2) * n)
        if n & (n - 1) == 0:
            puiss.append(n.bit_length() - 1)
    print("   addition : FRACTRAN et Collatz d'accord pour a, b < 6 :", ok)
    print("   PRIMEGAME vu comme fonction de Collatz (modulo", M2, ") : puissances de 2 atteintes :", puiss[:6])
    # 2. instance de Post (a/baa, ab/aa, bba/bb), solution 3,2,3,1
    dom = [('a', 'baa'), ('ab', 'aa'), ('bba', 'bb')]
    sol = [3, 2, 3, 1]
    P = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    for i in reversed(sol):            # le produit M_{i_m} ... M_{i_1} lit les mots dans l'ordre
        P = mul(P, matrice(*dom[i - 1]))
    print("2. Post : u =", ''.join(dom[i - 1][0] for i in sol), " v =", ''.join(dom[i - 1][1] for i in sol),
          "; coefficients (1,3) et (2,3) du produit :", P[0][2], P[1][2])
    # 3. tuiles : une machine qui s'arrête après 3 pas, une qui va à droite pour toujours
    arret = {('A', '0'): ('B', '1', 'D'), ('B', '0'): ('C', '1', 'D'), ('C', '0'): ('H', '1', 'D')}
    boucle = {('A', '0'): ('A', '1', 'D')}
    for nom, d in [("s'arrête en 3 pas", arret), ("ne s'arrête pas", boucle)]:
        T, o = tuiles(d, 'A')
        print(f"3. machine qui {nom} :", len(T), "tuiles ; carrés pavables :",
              [k for k in range(1, 8) if pave_carre(T, o, k)])
