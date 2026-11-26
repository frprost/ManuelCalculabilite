#!/usr/bin/env python3
"""Fonctions récursives : les termes du chapitre 4 du manuel, leur évaluation, une bibliothèque.

Un terme est construit avec exactement les briques de la définition :
    C(k, m)            constante m d'arité k        (x1..xk) -> m
    S                  successeur                   x -> x+1
    A(k, i)            projection (choix d'argument) (x1..xk) -> xi
    sigma(g, h1..hk)   substitution                 x -> g(h1(x), ..., hk(x))
    rho(g, h)          récursion primitive          f(0,x)=g(x), f(y+1,x)=h(y, f(y,x), x)
    mu(g)              minimisation                 x -> le plus petit y tel que g(x, y) = 0

La même syntaxe s'écrit en texte et se lit avec lire_terme :
    rho[A(1,1), sigma[S, A(3,2)]]        (l'addition)
On peut aussi écrire ρ, σ, μ et utiliser les noms de la bibliothèque (add, mult, ...).

Accélération. Les fonctions de la bibliothèque sont des termes Nomme(nom, terme, natif) :
le terme est la vraie définition, natif est une fonction Python qui calcule la même chose
plus vite. evaluer(t, args) utilise le terme ; evaluer(t, args, rapide=True) utilise natif
pour les sous-termes nommés. Le fichier tests.py vérifie que les deux coïncident.

    python3 recursives.py "rho[A(1,1), sigma[S, A(3,2)]]" 2 3     -> 5
    python3 recursives.py mult 4 5                                 -> 20
    python3 recursives.py --liste                                  bibliothèque

Licence MIT. Frédéric Prost et Claude.
"""
import re
import sys


class Diverge(RuntimeError):
    """Levée quand une minimisation dépasse la limite fixée (la fonction n'est peut-être pas définie)."""


class Terme:
    def __call__(self, *args, rapide=True):
        return evaluer(self, args, rapide=rapide)


class Const(Terme):
    def __init__(self, k, m):
        self.k, self.m = k, m

    def arite(self):
        return self.k

    def __str__(self):
        return "C(%d,%d)" % (self.k, self.m)


class Succ(Terme):
    def arite(self):
        return 1

    def __str__(self):
        return "S"


class Proj(Terme):
    def __init__(self, k, i):
        if not 1 <= i <= k:
            raise ValueError("projection A(%d,%d) impossible" % (k, i))
        self.k, self.i = k, i

    def arite(self):
        return self.k

    def __str__(self):
        return "A(%d,%d)" % (self.k, self.i)


class Comp(Terme):
    def __init__(self, g, *hs):
        if not hs:
            raise ValueError("sigma demande au moins une fonction intérieure")
        m = hs[0].arite()
        if any(h.arite() != m for h in hs):
            raise ValueError("sigma : les fonctions intérieures n'ont pas toutes la même arité")
        if g.arite() != len(hs):
            raise ValueError("sigma : %s est d'arité %d mais reçoit %d arguments" % (g, g.arite(), len(hs)))
        self.g, self.hs = g, hs

    def arite(self):
        return self.hs[0].arite()

    def __str__(self):
        return "sigma[%s]" % ", ".join(str(t) for t in (self.g,) + self.hs)


class Rec(Terme):
    def __init__(self, g, h):
        if h.arite() != g.arite() + 2:
            raise ValueError("rho : h doit avoir l'arité de g plus 2")
        self.g, self.h = g, h

    def arite(self):
        return self.g.arite() + 1

    def __str__(self):
        return "rho[%s, %s]" % (self.g, self.h)


class Mu(Terme):
    def __init__(self, g):
        if g.arite() < 1:
            raise ValueError("mu : g doit avoir au moins un argument")
        self.g = g

    def arite(self):
        return self.g.arite() - 1

    def __str__(self):
        return "mu[%s]" % self.g


class Nomme(Terme):
    """Un terme muni d'un nom et (facultativement) d'une version native plus rapide."""

    def __init__(self, nom, terme, natif=None):
        self.nom, self.terme, self.natif = nom, terme, natif

    def arite(self):
        return self.terme.arite()

    def __str__(self):
        return self.nom


S = Succ()


def C(k, m):
    return Const(k, m)


def A(k, i):
    return Proj(k, i)


def sigma(g, *hs):
    return Comp(g, *hs)


def rho(g, h):
    return Rec(g, h)


def mu(g):
    return Mu(g)


# ------------------------------------------------------------------ évaluation
LIMITE_MU = [10**6]


def evaluer(t, args, rapide=False):
    """Valeur de t en args. Pour une minimisation, lève Diverge au-delà de LIMITE_MU[0] essais."""
    args = tuple(args)
    if len(args) != t.arite():
        raise ValueError("%s est d'arité %d, reçoit %d arguments" % (t, t.arite(), len(args)))
    return _ev(t, args, rapide)


def _ev(t, args, rapide):
    while isinstance(t, Nomme):
        if rapide and t.natif is not None:
            return t.natif(*args)
        t = t.terme
    if isinstance(t, Const):
        return t.m
    if isinstance(t, Succ):
        return args[0] + 1
    if isinstance(t, Proj):
        return args[t.i - 1]
    if isinstance(t, Comp):
        return _ev(t.g, tuple(_ev(h, args, rapide) for h in t.hs), rapide)
    if isinstance(t, Rec):
        y, reste = args[0], args[1:]
        acc = _ev(t.g, reste, rapide)
        for i in range(y):                     # la boucle « pour » : y tours connus d'avance
            acc = _ev(t.h, (i, acc) + reste, rapide)
        return acc
    if isinstance(t, Mu):
        z = 0
        while True:                            # la boucle « tant que » : nombre de tours inconnu
            if _ev(t.g, args + (z,), rapide) == 0:
                return z
            z += 1
            if z > LIMITE_MU[0]:
                raise Diverge("minimisation sans réponse après %d essais" % LIMITE_MU[0])
    raise TypeError("terme inconnu : %r" % (t,))


def deplier(t):
    """Le terme sans aucun nom : uniquement C, S, A, sigma, rho, mu."""
    if isinstance(t, Nomme):
        return deplier(t.terme)
    if isinstance(t, Comp):
        return Comp(deplier(t.g), *[deplier(h) for h in t.hs])
    if isinstance(t, Rec):
        return Rec(deplier(t.g), deplier(t.h))
    if isinstance(t, Mu):
        return Mu(deplier(t.g))
    return t


def taille(t):
    """Nombre de briques du terme entièrement déplié (les sous-termes partagés comptent à chaque usage)."""
    memo = {}

    def go(u):
        if id(u) in memo:
            return memo[id(u)]
        if isinstance(u, Nomme):
            r = go(u.terme)
        elif isinstance(u, Comp):
            r = 1 + go(u.g) + sum(go(h) for h in u.hs)
        elif isinstance(u, Rec):
            r = 1 + go(u.g) + go(u.h)
        elif isinstance(u, Mu):
            r = 1 + go(u.g)
        else:
            r = 1
        memo[id(u)] = r
        return r
    return go(t)


def est_primitif(t):
    """Vrai si le terme n'utilise pas mu (il définit alors une fonction totale)."""
    if isinstance(t, Nomme):
        return est_primitif(t.terme)
    if isinstance(t, Mu):
        return False
    if isinstance(t, Comp):
        return est_primitif(t.g) and all(est_primitif(h) for h in t.hs)
    if isinstance(t, Rec):
        return est_primitif(t.g) and est_primitif(t.h)
    return True


# ------------------------------------------------------------------ bibliothèque
BIB = {}


def definir(nom, terme, natif=None):
    t = Nomme(nom, terme, natif)
    BIB[nom] = t
    return t


def P(k, i):
    return A(k, i)


# Opérations de base (chapitre 4, « Addition, multiplication, ... »)
add = definir("add", rho(A(1, 1), sigma(S, A(3, 2))), lambda x, y: x + y)
mult = definir("mult", rho(C(1, 0), sigma(add, A(3, 3), A(3, 2))), lambda x, y: x * y)
pred = definir("pred", rho(C(0, 0), A(2, 1)), lambda x: max(x - 1, 0))
# moins_inv(y, x) = x ∸ y (récurrence sur le premier argument), puis on échange
moins_inv = definir("moins_inv", rho(A(1, 1), sigma(pred, A(3, 2))), lambda y, x: max(x - y, 0))
monus = definir("monus", sigma(moins_inv, A(2, 2), A(2, 1)), lambda x, y: max(x - y, 0))
sg = definir("sg", rho(C(0, 0), C(2, 1)), lambda x: 1 if x else 0)
sgbar = definir("sgbar", rho(C(0, 1), C(2, 0)), lambda x: 0 if x else 1)
puiss_inv = definir("puiss_inv", rho(C(1, 1), sigma(mult, A(3, 3), A(3, 2))), lambda y, x: x ** y)
puiss = definir("puiss", sigma(puiss_inv, A(2, 2), A(2, 1)), lambda x, y: x ** y)
fact = definir("fact", rho(C(0, 1), sigma(mult, sigma(S, A(2, 1)), A(2, 2))),
               lambda x: __import__("math").factorial(x))
# distance |x - y| et égalité
dist = definir("dist", sigma(add, monus, sigma(monus, A(2, 2), A(2, 1))), lambda x, y: abs(x - y))
eg = definir("eg", sigma(sgbar, dist), lambda x, y: 1 if x == y else 0)
# inférieur strict : x < y  ssi  y ∸ x > 0
inf = definir("inf", sigma(sg, sigma(monus, A(2, 2), A(2, 1))), lambda x, y: 1 if x < y else 0)
# connecteurs sur les valeurs de vérité 0/1
et = definir("et", mult, lambda a, b: a * b)
non = definir("non", sgbar, lambda a: 0 if a else 1)
ou = definir("ou", sigma(sg, add), lambda a, b: 1 if (a or b) else 0)
# si(c, a, b) = a si c ≠ 0, b sinon : a·sg(c) + b·sgbar(c)
si = definir("si", sigma(add, sigma(mult, A(3, 2), sigma(sg, A(3, 1))), sigma(mult, A(3, 3), sigma(sgbar, A(3, 1)))),
             lambda c, a, b: a if c else b)
# quotient et reste. quot_inv(y, x) : récurrence sur y du couple implicite :
#   q(0, x) = 0 ; q(y+1, x) = q(y, x) + [ (y+1) est un multiple de x ]   -> q(y, x) = y div x  (x > 0)
# reste : r(0,x) = 0 ; r(y+1,x) = si (r(y,x)+1 = x) alors 0 sinon r(y,x)+1
reste_inv = definir("reste_inv",
                    rho(C(1, 0), sigma(si, sigma(eg, sigma(S, A(3, 2)), A(3, 3)), C(3, 0), sigma(S, A(3, 2)))),
                    lambda y, x: y % x if x else y)
quot_inv = definir("quot_inv",
                   rho(C(1, 0), sigma(add, A(3, 2), sigma(eg, sigma(S, sigma(reste_inv, A(3, 1), A(3, 3))), A(3, 3)))),
                   lambda y, x: y // x if x else 0)
reste = definir("reste", sigma(reste_inv, A(2, 1), A(2, 2)), lambda x, y: x % y if y else x)
quot = definir("quot", sigma(quot_inv, A(2, 1), A(2, 2)), lambda x, y: x // y if y else 0)
# quotient par minimisation (non borné : indéfini pour y = 0), comme dans le manuel
div = definir("div", mu(sigma(sgbar, sigma(monus, sigma(mult, sigma(S, A(3, 3)), A(3, 2)), A(3, 1)))),
              None)
# fonction partout indéfinie
vide = definir("vide", mu(C(2, 1)), None)

# Couples de Cantor : <x, y> = (x+y)(x+y+1)/2 + x   (chapitre 4, « Codage de Cantor des couples »)
# tri(n) = n(n+1)/2 ; tri(0) = 0, tri(n+1) = tri(n) + n + 1
tri = definir("tri", rho(C(0, 0), sigma(add, A(2, 2), sigma(S, A(2, 1)))), lambda n: n * (n + 1) // 2)
couple = definir("couple", sigma(add, sigma(tri, add), A(2, 1)), lambda x, y: (x + y) * (x + y + 1) // 2 + x)


def _racine_tri(z):
    """Le plus grand n tel que tri(n) <= z."""
    from math import isqrt
    return (isqrt(8 * z + 1) - 1) // 2


# diag(z) = le plus grand n tel que tri(n) <= z (c'est x + y), obtenu par récurrence :
# diag(0) = 0 ; diag(z+1) = diag(z) + [tri(diag(z)+1) = z+1]
diag = definir("diag", rho(C(0, 0), sigma(add, A(2, 2), sigma(eg, sigma(tri, sigma(S, A(2, 2))), sigma(S, A(2, 1))))),
               _racine_tri)
# gauche(z) = pi_1(z) = z ∸ tri(diag(z)) ; droite(z) = pi_2(z) = diag(z) ∸ gauche(z)
gauche = definir("gauche", sigma(monus, A(1, 1), sigma(tri, diag)),
                 lambda z: z - _racine_tri(z) * (_racine_tri(z) + 1) // 2)
droite = definir("droite", sigma(monus, diag, gauche),
                 lambda z: _racine_tri(z) - (z - _racine_tri(z) * (_racine_tri(z) + 1) // 2))


def cantor(x, y):
    return (x + y) * (x + y + 1) // 2 + x


def decantor(z):
    n = _racine_tri(z)
    x = z - n * (n + 1) // 2
    return x, n - x


# ------------------------------------------------------------------ écriture commode : substitution générale
# La proposition « substitution générale » du chapitre 4 dit qu'on peut écrire
#     f(x, y) = g(y, h(x, x), 3)
# sans passer explicitement par les projections : on les ajoute mécaniquement.
# `fonction` fait exactement cette traduction :
#     f = fonction(2, lambda x, y: App(g, y, App(h, x, x), 3))
# donne le terme sigma[g, A(2,2), sigma[h, A(2,1), A(2,1)], C(2,3)].

class Expr:
    def __call__(self, *a):
        raise TypeError("une expression ne s'applique pas")


class Var(Expr):
    def __init__(self, i):
        self.i = i


class App(Expr):
    def __init__(self, f, *args):
        if f.arite() != len(args):
            raise ValueError("%s attend %d arguments, en reçoit %d" % (f, f.arite(), len(args)))
        self.f, self.args = f, args


def _traduire(e, k):
    if isinstance(e, int):
        return C(k, e)
    if isinstance(e, Var):
        return A(k, e.i)
    if isinstance(e, App):
        if e.f.arite() == 0:
            raise ValueError("appliquer une fonction d'arité 0 : écrire sa valeur")
        return Comp(e.f, *[_traduire(a, k) for a in e.args])
    raise TypeError("expression inconnue : %r" % (e,))


def fonction(k, corps, nom=None, natif=None):
    """Le terme d'arité k défini par corps(x1, ..., xk) (une expression faite de App, de variables et d'entiers)."""
    e = corps(*[Var(i) for i in range(1, k + 1)])
    if isinstance(e, Var) and k >= 1:
        t = A(k, e.i)
    else:
        t = _traduire(e, k)
    return definir(nom, t, natif) if nom else t


def recurrence(k, base, pas, nom=None, natif=None):
    """f(0, x2..xk) = base(x2..xk) ; f(y+1, x2..xk) = pas(y, f(y, x), x2..xk).
    base et pas sont des fonctions Python qui renvoient des expressions."""
    g = fonction(k - 1, base) if k > 1 else C(0, base())
    h = fonction(k + 1, pas)
    t = rho(g, h)
    return definir(nom, t, natif) if nom else t


def minimisation(k, corps, nom=None, natif=None):
    """f(x1..xk) = le plus petit z tel que corps(x1..xk, z) = 0."""
    t = mu(fonction(k + 1, corps))
    return definir(nom, t, natif) if nom else t


# ------------------------------------------------------------------ lecture d'un terme écrit en texte
_JETONS = re.compile(r"\s*(?:(\d+)|([A-Za-zÀ-ÿσρμ_][A-Za-z0-9À-ÿ_]*)|(.))")


def lire_terme(texte, definitions=None):
    """Lit un terme écrit comme dans le manuel : rho[A(1,1), sigma[S, A(3,2)]].
    Les noms de la bibliothèque et ceux de `definitions` sont reconnus."""
    env = dict(BIB)
    if definitions:
        env.update(definitions)
    jetons = [m.group(1) or m.group(2) or m.group(3) for m in _JETONS.finditer(texte) if (m.group(0).strip())]
    pos = [0]

    def voir():
        return jetons[pos[0]] if pos[0] < len(jetons) else None

    def prendre(attendu=None):
        j = voir()
        if attendu is not None and j != attendu:
            raise SyntaxError("attendu « %s », trouvé « %s »" % (attendu, j))
        pos[0] += 1
        return j

    def entier():
        j = prendre()
        if not j or not j.isdigit():
            raise SyntaxError("entier attendu, trouvé « %s »" % j)
        return int(j)

    def terme():
        j = prendre()
        if j in ("S",):
            return S
        if j in ("C", "A"):
            prendre("(")
            a = entier()
            prendre(",")
            b = entier()
            prendre(")")
            return C(a, b) if j == "C" else A(a, b)
        if j in ("sigma", "σ", "rho", "ρ", "mu", "μ"):
            prendre("[")
            ts = [terme()]
            while voir() == ",":
                prendre(",")
                ts.append(terme())
            prendre("]")
            if j in ("sigma", "σ"):
                return Comp(ts[0], *ts[1:])
            if j in ("rho", "ρ"):
                if len(ts) != 2:
                    raise SyntaxError("rho prend deux termes")
                return Rec(*ts)
            if len(ts) != 1:
                raise SyntaxError("mu prend un terme")
            return Mu(ts[0])
        if j in env:
            return env[j]
        raise SyntaxError("symbole inconnu « %s »" % j)

    t = terme()
    if voir() is not None:
        raise SyntaxError("texte en trop après le terme : « %s »" % voir())
    return t


def lire_programme(texte):
    """Lit des lignes « nom = terme » ; la dernière ligne sans « = » est le terme à calculer."""
    defs, dernier = {}, None
    for ligne in texte.splitlines():
        ligne = ligne.split("#", 1)[0].strip()
        if not ligne:
            continue
        if "=" in ligne:
            nom, corps = [s.strip() for s in ligne.split("=", 1)]
            defs[nom] = Nomme(nom, lire_terme(corps, defs))
            dernier = defs[nom]
        else:
            dernier = lire_terme(ligne, defs)
    return defs, dernier


def _principal(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    if argv[1] == "--liste":
        for nom, t in BIB.items():
            print("%-10s arité %d   %s" % (nom, t.arite(), t.terme))
        return 0
    t = lire_terme(argv[1])
    args = [int(a) for a in argv[2:]]
    print("terme      :", deplier(t))
    print("arité      :", t.arite(), "   taille :", taille(t), "briques")
    print("valeur     :", evaluer(t, args))
    return 0


if __name__ == "__main__":
    sys.exit(_principal(sys.argv))
