#!/usr/bin/env python3
"""λ-calcul : réduction en ordre normal, entiers de Church, et compilateur
fonctions récursives -> λ-termes (chapitres « λ-calcul » et « Équivalence » du manuel).

Syntaxe (la même que le réducteur intégré aux pages) :
    λx.M  ou  \\x.M        abstraction ; λx y.M abrège λx.λy.M
    M N                    application (à gauche : M N P = (M N) P)
    0, 1, 2, ...           entiers de Church : n = λf x.f (f (... (f x)))
    NOM = terme            définition (une par ligne), utilisable ensuite

Le compilateur suit la démonstration du théorème « les fonctions récursives sont λ-définissables » :
    C(k,m)       -> λx1..xk. m
    S            -> λn f x. f (n f x)
    A(k,i)       -> λx1..xk. xi
    sigma[g,h..] -> λx. G (H1 x) ... (Hk x)
    rho[g,h]     -> λy x. snd (y (λp. pair (S (fst p)) (H (fst p) (snd p) x)) (pair 0 (G x)))
    mu[g]        -> λx. Θ (λr m. zero? (G x m) m (r (S m))) 0        (Θ : combinateur de Turing)

Utilisation :
    python3 lambda_calcul.py "(λm n f.m (n f)) 2 3"          réduit le terme : 6
    python3 lambda_calcul.py --fichier programme.lam
    python3 lambda_calcul.py --compiler mult 2 3              fonction récursive -> λ-terme, réduit

Licence MIT. Frédéric Prost et Claude.
"""
import re
import sys

sys.setrecursionlimit(100000)

# ------------------------------------------------------------------ termes nommés
# ('v', nom) | ('l', nom, corps) | ('a', fonction, argument)


def V(n):
    return ("v", n)


def L(noms, corps):
    for n in reversed(noms.split()):
        corps = ("l", n, corps)
    return corps


def Ap(*ts):
    t = ts[0]
    for u in ts[1:]:
        t = ("a", t, u)
    return t


def church(n):
    corps = V("x")
    for _ in range(n):
        corps = Ap(V("f"), corps)
    return L("f x", corps)


# ------------------------------------------------------------------ lecture
def _jetons(s):
    for m in re.finditer(r"\s*(λ|\\|\(|\)|\.|[A-Za-z0-9_'?+*\-]+)", s):
        yield m.group(1)


def lire(s, defs=None):
    defs = defs or {}
    toks = list(_jetons(s))
    pos = [0]

    def voir():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def terme():
        if voir() in ("λ", "\\"):
            pos[0] += 1
            noms = []
            while voir() not in (".", None):
                noms.append(toks[pos[0]])
                pos[0] += 1
            if voir() != "." or not noms:
                raise SyntaxError("abstraction mal formée")
            pos[0] += 1
            return L(" ".join(noms), terme())
        t = atome()
        while voir() not in (None, ")"):
            if voir() in ("λ", "\\"):
                return Ap(t, terme())
            t = Ap(t, atome())
        return t

    def atome():
        j = voir()
        pos[0] += 1
        if j == "(":
            t = terme()
            if voir() != ")":
                raise SyntaxError("parenthèse non fermée")
            pos[0] += 1
            return t
        if j is None or j in (")", "."):
            raise SyntaxError("terme attendu")
        if j.isdigit():
            return church(int(j))
        if j in defs:
            return defs[j]
        return V(j)

    t = terme()
    if voir() is not None:
        raise SyntaxError("texte en trop : %s" % voir())
    return t


def lire_programme(texte):
    defs, t = {}, None
    for ligne in texte.splitlines():
        ligne = ligne.split("#", 1)[0].strip()
        if not ligne:
            continue
        m = re.match(r"^([A-Za-z0-9_'?+*\-]+)\s*=\s*(.*)$", ligne)
        if m:
            defs[m.group(1)] = lire(m.group(2), defs)
        else:
            t = lire(ligne, defs)
    return t


# ------------------------------------------------------------------ indices de de Bruijn
# ('V', k) | ('L', corps) | ('A', f, x)

def vers_db(t, env=()):
    if t[0] == "v":
        if t[1] in env:
            return ("V", env.index(t[1]))
        raise ValueError("variable libre : %s" % t[1])
    if t[0] == "l":
        return ("L", vers_db(t[2], (t[1],) + env))
    return ("A", vers_db(t[1], env), vers_db(t[2], env))


def decaler(t, d, c=0):
    if t[0] == "V":
        return ("V", t[1] + d) if t[1] >= c else t
    if t[0] == "L":
        return ("L", decaler(t[1], d, c + 1))
    return ("A", decaler(t[1], d, c), decaler(t[2], d, c))


def substituer(t, j, s):
    if t[0] == "V":
        if t[1] == j:
            return decaler(s, j)
        return ("V", t[1] - 1) if t[1] > j else t
    if t[0] == "L":
        return ("L", substituer(t[1], j + 1, s))
    return ("A", substituer(t[1], j, s), substituer(t[2], j, s))


def pas_normal(t):
    """Un pas de réduction gauche-externe ; None si t est normal."""
    if t[0] == "A":
        if t[1][0] == "L":
            return substituer(t[1][1], 0, t[2])
        f = pas_normal(t[1])
        if f is not None:
            return ("A", f, t[2])
        x = pas_normal(t[2])
        return None if x is None else ("A", t[1], x)
    if t[0] == "L":
        b = pas_normal(t[1])
        return None if b is None else ("L", b)
    return None


def normaliser(t, max_pas=10**6):
    """Forme normale par la stratégie normale (qui la trouve toujours si elle existe).
    Renvoie (forme normale, nombre de pas) ; lève RuntimeError au-delà de max_pas."""
    if t[0] in ("v", "l", "a"):
        t = vers_db(t)
    n = 0
    while True:
        u = pas_normal(t)
        if u is None:
            return t, n
        t, n = u, n + 1
        if n >= max_pas:
            raise RuntimeError("pas de forme normale après %d pas" % max_pas)


def entier(t):
    """L'entier n si t est (en de Bruijn) le numéral de Church λf.λx.f^n x, sinon None."""
    if t[0] != "L" or t[1][0] != "L":
        return None
    c, n = t[1][1], 0
    while c[0] == "A" and c[1] == ("V", 1):
        c, n = c[2], n + 1
    return n if c == ("V", 0) else None


def afficher(t, noms=None, prof=0):
    """Écriture lisible d'un terme en de Bruijn."""
    if t[0] == "V":
        return noms[-1 - t[1]] if noms and t[1] < len(noms) else "#%d" % t[1]
    noms = noms or []
    if t[0] == "L":
        x = "x%d" % (len(noms))
        return "λ%s.%s" % (x, afficher(t[1], noms + [x]))
    f = afficher(t[1], noms)
    a = afficher(t[2], noms)
    if t[1][0] == "L":
        f = "(%s)" % f
    if t[2][0] != "V":
        a = "(%s)" % a
    return "%s %s" % (f, a)


# ------------------------------------------------------------------ bibliothèque et compilateur
PRELUDE = """tt = λx y.x
ff = λx y.y
S = λn f x.f (n f x)
zero? = λn.n (λz.ff) tt
pair = λa b s.s a b
fst = λp.p tt
snd = λp.p ff
Θ = (λx y.y (x x y)) (λx y.y (x x y))
"""
_P = {}
for _l in PRELUDE.splitlines():
    _n, _c = _l.split(" = ")
    _P[_n] = lire(_c, _P)

_compteur = [0]


def _vars(k, prefixe="x"):
    _compteur[0] += 1
    return ["%s%d_%d" % (prefixe, i, _compteur[0]) for i in range(1, k + 1)]


def compiler(f):
    """λ-terme (nommé) qui λ-définit la fonction récursive f."""
    from recursives import Const, Succ, Proj, Comp, Rec, Mu, Nomme
    while isinstance(f, Nomme):
        f = f.terme
    if isinstance(f, Const):
        xs = _vars(f.k)
        return L(" ".join(xs), church(f.m)) if xs else church(f.m)
    if isinstance(f, Succ):
        return _P["S"]
    if isinstance(f, Proj):
        xs = _vars(f.k)
        return L(" ".join(xs), V(xs[f.i - 1]))
    if isinstance(f, Comp):
        xs = _vars(f.arite())
        G = compiler(f.g)
        args = [Ap(compiler(h), *[V(x) for x in xs]) for h in f.hs]
        return L(" ".join(xs), Ap(G, *args))
    if isinstance(f, Rec):
        G, H = compiler(f.g), compiler(f.h)
        y = _vars(1, "y")[0]
        xs = _vars(f.arite() - 1)
        p = _vars(1, "p")[0]
        fst, snd, pair, S = _P["fst"], _P["snd"], _P["pair"], _P["S"]
        X = [V(x) for x in xs]
        pas = L(p, Ap(pair, Ap(S, Ap(fst, V(p))), Ap(H, Ap(fst, V(p)), Ap(snd, V(p)), *X)))
        depart = Ap(pair, church(0), Ap(G, *X) if X else G)
        return L(" ".join([y] + xs), Ap(snd, Ap(V(y), pas, depart)))
    if isinstance(f, Mu):
        G = compiler(f.g)
        xs = _vars(f.arite())
        rr, m = _vars(1, "r")[0], _vars(1, "m")[0]
        X = [V(x) for x in xs]
        W = L("%s %s" % (rr, m), Ap(_P["zero?"], Ap(G, *(X + [V(m)])), V(m), Ap(V(rr), Ap(_P["S"], V(m)))))
        corps = Ap(_P["Θ"], W, church(0))
        return L(" ".join(xs), corps) if xs else corps
    raise TypeError("terme inconnu")


def calculer(f, *args, max_pas=10**6):
    """Réduit (compiler(f)) n1 ... nk et lit l'entier obtenu."""
    t = Ap(compiler(f), *[church(a) for a in args])
    nf, n = normaliser(t, max_pas)
    return entier(nf), n


def _principal(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    if argv[1] == "--compiler":
        from recursives import lire_terme
        f = lire_terme(argv[2])
        args = [int(a) for a in argv[3:]]
        v, n = calculer(f, *args)
        print("valeur : %s   (%d pas de β-réduction)" % (v, n))
        return 0
    if argv[1] == "--fichier":
        with open(argv[2], encoding="utf-8") as fh:
            t = lire_programme(PRELUDE + fh.read())
    else:
        t = lire_programme(PRELUDE + argv[1])
    nf, n = normaliser(t)
    e = entier(nf)
    print("forme normale : %s" % afficher(nf))
    print("(%d pas)%s" % (n, "   entier de Church : %d" % e if e is not None else ""))
    return 0


if __name__ == "__main__":
    sys.exit(_principal(sys.argv))
