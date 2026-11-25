"""Décider l'arithmétique de Presburger avec des automates (chapitre « Théories décidables »).

Un n-uplet d'entiers est écrit en binaire, bit de poids faible en tête : la k-ième lettre
du mot est le n-uplet des k-ièmes bits. Chaque formule devient un automate fini déterministe
qui reconnaît exactement les écritures des n-uplets qui la satisfont (zéros finals compris).

Formules : ('eq', {x: a, y: b, ...}, c) pour a*x + b*y + ... = c (coefficients entiers) ;
('le', {...}, c) pour a*x + ... <= c ; ('non', A) ; ('et', A, B) ; ('ou', A, B) ;
('imp', A, B) ; ('ex', x, A) ; ('tout', x, A).
"""
from itertools import product


class AFD:
    """Automate déterministe complet sur l'alphabet {0,1}^len(vars)."""
    def __init__(self, vars_, init, delta, acc):
        self.vars, self.init, self.delta, self.acc = tuple(vars_), init, delta, acc

    def lettres(self):
        return list(product((0, 1), repeat=len(self.vars)))


def explorer(vars_, init, pas, accepte):
    """Construit l'automate accessible à partir d'une fonction de transition."""
    lettres = list(product((0, 1), repeat=len(vars_)))
    delta, acc, a_voir = {}, set(), [init]
    vus = {init}
    while a_voir:
        q = a_voir.pop()
        if accepte(q):
            acc.add(q)
        for l in lettres:
            r = pas(q, l)
            delta[q, l] = r
            if r not in vus:
                vus.add(r)
                a_voir.append(r)
    return AFD(vars_, init, delta, acc)


def atome(coefs, c, egal):
    vars_ = sorted(coefs)
    a = [coefs[v] for v in vars_]

    def pas(q, l):
        if q is None:
            return None
        s = q - sum(ai * bi for ai, bi in zip(a, l))
        if egal:
            return s // 2 if s % 2 == 0 else None     # None : état puits
        return s // 2                                  # partie entière inférieure

    def accepte(q):
        return q is not None and (q == 0 if egal else q >= 0)
    return explorer(vars_, c, pas, accepte)


def etendre(A, vars_):
    """Même automate, lu sur plus de pistes (les pistes en plus sont ignorées)."""
    pos = [vars_.index(v) for v in A.vars]
    return explorer(vars_, A.init,
                    lambda q, l: A.delta[q, tuple(l[i] for i in pos)],
                    lambda q: q in A.acc)


def produit(A, B, op):
    vars_ = sorted(set(A.vars) | set(B.vars))
    A, B = etendre(A, vars_), etendre(B, vars_)
    return explorer(vars_, (A.init, B.init),
                    lambda q, l: (A.delta[q[0], l], B.delta[q[1], l]),
                    lambda q: op(q[0] in A.acc, q[1] in B.acc))


def complement(A):
    return AFD(A.vars, A.init, A.delta, set(q for q, _ in A.delta) - A.acc | ({A.init} - A.acc))


def projeter(A, x):
    """Automate de ∃x A : on efface la piste x (sous-ensembles), puis on accepte aussi
    les ensembles d'où des lettres nulles mènent à l'acceptation (le témoin x peut
    avoir plus de bits que les autres variables)."""
    if x not in A.vars:
        return A
    i = A.vars.index(x)
    vars_ = A.vars[:i] + A.vars[i + 1:]

    def pas(S, l):
        return frozenset(A.delta[q, l[:i] + (b,) + l[i:]] for q in S for b in (0, 1))
    B = explorer(vars_, frozenset([A.init]), pas, lambda S: bool(S & A.acc))
    zero = tuple(0 for _ in vars_)
    acc, change = set(B.acc), True
    while change:
        change = False
        for (S, l), T in B.delta.items():
            if l == zero and T in acc and S not in acc:
                acc.add(S)
                change = True
    B.acc = acc
    return B


def automate(f):
    op = f[0]
    if op in ('eq', 'le'):
        return atome({v: a for v, a in f[1].items() if a}, f[2], op == 'eq')
    if op == 'non':
        return complement(automate(f[1]))
    if op == 'et':
        return produit(automate(f[1]), automate(f[2]), lambda a, b: a and b)
    if op == 'ou':
        return produit(automate(f[1]), automate(f[2]), lambda a, b: a or b)
    if op == 'imp':
        return produit(automate(f[1]), automate(f[2]), lambda a, b: (not a) or b)
    if op == 'ex':
        return projeter(automate(f[2]), f[1])
    if op == 'tout':
        return complement(projeter(complement(automate(f[2])), f[1]))
    raise ValueError(op)


def vrai(enonce):
    A = automate(enonce)
    assert A.vars == (), "l'énoncé a des variables libres"
    return A.init in A.acc


def accepte(A, valeurs):
    """L'automate accepte-t-il l'écriture binaire du n-uplet (dans l'ordre de A.vars) ?"""
    q, n = A.init, max([v.bit_length() for v in valeurs] + [0])
    for k in range(n):
        q = A.delta[q, tuple((v >> k) & 1 for v in valeurs)]
    return q in A.acc


if __name__ == "__main__":
    import random
    # 1. contrôle des automates d'atomes et des connecteurs contre un calcul direct
    random.seed(1)
    for _ in range(300):
        a, b, c, d = (random.randint(-3, 3) for _ in range(4))
        f = ('ou', ('eq', {'x': a, 'y': b}, c), ('non', ('le', {'x': b, 'y': d}, a)))
        A = automate(f)
        for x in range(12):
            for y in range(12):
                env = {'x': x, 'y': y}
                attendu = (a * x + b * y == c) or not (b * x + d * y <= a)
                assert accepte(A, [env[v] for v in A.vars]) == attendu
    print("1. automates des formules sans quantificateur : conformes au calcul direct")
    # 2. quelques énoncés
    pair_ou_impair = ('tout', 'x', ('ex', 'y', ('ou', ('eq', {'x': 1, 'y': -2}, 0),
                                                 ('eq', {'x': 1, 'y': -2}, 1))))
    print("2. tout entier est pair ou impair :", vrai(pair_ou_impair))

    def monnaie(s):           # tout n >= s s'écrit 3a + 5b
        return ('tout', 'n', ('imp', ('le', {'n': -1}, -s),
                              ('ex', 'a', ('ex', 'b', ('eq', {'n': 1, 'a': -3, 'b': -5}, 0)))))
    print("   tout n >= 8 s'écrit 3a+5b :", vrai(monnaie(8)), "; tout n >= 7 :", vrai(monnaie(7)))
    print("   il existe x avec 2x = 5 :", vrai(('ex', 'x', ('eq', {'x': 2}, 5))))
    print("   pas de plus grand entier :", vrai(('tout', 'x', ('ex', 'y', ('le', {'x': 1, 'y': -1}, -1)))))
    # 3. une contrainte de contrôle : 3 | x et 5 | x  <=>  15 | x
    div = lambda m, v, w: ('ex', w, ('eq', {v: 1, w: -m}, 0))
    print("3. (3 | x et 5 | x) <=> 15 | x :", vrai(('tout', 'x', ('et',
          ('imp', ('et', div(3, 'x', 'u'), div(5, 'x', 'v')), div(15, 'x', 'w')),
          ('imp', div(15, 'x', 'w'), ('et', div(3, 'x', 'u'), div(5, 'x', 'v')))))))
    A = automate(('ex', 'y', ('eq', {'x': 1, 'y': -3}, 0)))
    print("   automate des multiples de 3 :", len({q for q, _ in A.delta}), "états")
