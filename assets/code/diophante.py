"""Équations diophantiennes : trois expériences (chapitre « Équations diophantiennes »).

1. La plus petite solution de x^2 - d y^2 = 1 (fractions continues) : sa taille saute
   d'un d à l'autre, ce qui illustre l'absence de borne calculable sur les solutions.
2. L'astuce de Putnam : les valeurs positives de a(1 - P(a, y)^2) forment l'ensemble
   diophantien défini par P ; essai avec les nombres qui ne sont pas des carrés.
3. Réduction au degré 4 : l'exemple 5x^3y^2 - 7z - 6w^2x + 9 = 0, transformé en un
   système d'équations de degré au plus 2, vérifié sur une grille de valeurs.
"""
from itertools import product
from math import isqrt


def pell(d):
    """Plus petite solution (x, y), y >= 1, de x^2 - d y^2 = 1, d non carré."""
    a0 = isqrt(d)
    m, q, a = 0, 1, a0
    p0, p1, q0, q1 = 1, a0, 0, 1
    while p1 * p1 - d * q1 * q1 != 1:
        m = q * a - m
        q = (d - m * m) // q
        a = (a0 + m) // q
        p0, p1 = p1, a * p1 + p0
        q0, q1 = q1, a * q1 + q0
    return p1, q1


def putnam_non_carres(borne):
    """Non-carrés : a = z^2 + x + 1 et (z+1)^2 = a + y + 1. Valeurs positives de a(1 - P^2)."""
    valeurs = set()
    for a, z, x, y in product(range(borne), repeat=4):
        P = (a - z * z - x - 1) ** 2 + ((z + 1) ** 2 - a - y - 1) ** 2
        Q = a * (1 - P * P)
        if Q > 0:
            valeurs.add(Q)
    return sorted(valeurs)


def systeme_degre_2(x, y, z, w):
    """Le système auxiliaire de l'exemple a-t-il une solution prolongeant (x, y, z, w) ?
    Les variables auxiliaires sont déterminées par les équations, on les calcule."""
    p1 = 5 * x; p2 = p1 * x; p3 = p2 * x; p4 = p3 * y; p5 = p4 * y   # 5x^3y^2
    q1 = 7 * z
    r1 = 6 * w; r2 = r1 * w; r3 = r2 * x                              # 6w^2x
    t1 = p5 + 9; t2 = q1 + r3
    return t1 == t2


if __name__ == "__main__":
    print("1. plus petite solution de x^2 - d y^2 = 1")
    for d in (13, 60, 61, 62, 109):
        x, y = pell(d)
        assert x * x - d * y * y == 1
        print(f"   d = {d:3d} : x = {x}, y = {y}")
    print("2. valeurs positives du polynôme de Putnam (inconnues < 12) :", putnam_non_carres(12)[:15], "...")
    accord = all(systeme_degre_2(*v) == (5 * v[0]**3 * v[1]**2 - 7 * v[2] - 6 * v[3]**2 * v[0] + 9 == 0)
                 for v in product(range(8), repeat=4))
    print("3. système de degré 2 et équation de départ : même ensemble de solutions sur [0,8)^4 :", accord)
