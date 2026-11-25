"""Logique et calcul : deux expériences (chapitre « Logique et types »).

1. Logique monadique : décider la satisfaisabilité d'un énoncé qui n'utilise que des
   prédicats unaires P1..Pk, en essayant toutes les structures à au plus 2^k éléments.
2. λ-calcul simplement typé et Système T : la fonction d'Ackermann écrite avec le
   récurseur de Gödel, à l'ordre supérieur, et comparée à la définition de Péter.
3. Système F : la même fonction avec les seuls entiers de Church polymorphes, sans
   récurseur, en itérant au type Nat -> Nat.

Formules : ('P', i, 'x') atome ; ('non', A) ; ('et', A, B) ; ('ou', A, B) ; ('imp', A, B) ;
('ex', 'x', A) ; ('tout', 'x', A).
"""
from itertools import product


def vrai(f, dom, interp, env):
    op = f[0]
    if op == 'P':
        return env[f[2]] in interp[f[1]]
    if op == 'non':
        return not vrai(f[1], dom, interp, env)
    if op == 'et':
        return vrai(f[1], dom, interp, env) and vrai(f[2], dom, interp, env)
    if op == 'ou':
        return vrai(f[1], dom, interp, env) or vrai(f[2], dom, interp, env)
    if op == 'imp':
        return (not vrai(f[1], dom, interp, env)) or vrai(f[2], dom, interp, env)
    if op == 'ex':
        return any(vrai(f[2], dom, interp, {**env, f[1]: d}) for d in dom)
    if op == 'tout':
        return all(vrai(f[2], dom, interp, {**env, f[1]: d}) for d in dom)
    raise ValueError(op)


def predicats(f):
    if f[0] == 'P':
        return {f[1]}
    return set().union(*(predicats(g) for g in f[1:] if isinstance(g, tuple)))


def satisfaisable(f):
    """Cherche un modèle de taille 1..2^k (k prédicats) : suffisant d'après le théorème."""
    ps = sorted(predicats(f))
    k = len(ps)
    for m in range(1, 2 ** k + 1):
        dom = range(m)
        for choix in product(product([False, True], repeat=m), repeat=k):
            interp = {p: {d for d in dom if choix[i][d]} for i, p in enumerate(ps)}
            if vrai(f, dom, interp, {}):
                return m, interp
    return None


def valide(f):
    return satisfaisable(('non', f)) is None


# Système T, simulé en Python : R a g n avec R a g 0 = a, R a g (n+1) = g n (R a g n)
def R(a, g, n):
    acc = a
    for k in range(n):
        acc = g(k, acc)
    return acc


def iter_(n, f, a):              # f^n(a) = R a (λk.f) n
    return R(a, lambda k, acc: f(acc), n)


succ = lambda n: n + 1
# ack m = R succ (λk.λf.λn. iter (n+1) f 1) m   (récursion au type Nat -> Nat)
ack = lambda m: R(succ, lambda k, f: (lambda n: iter_(n + 1, f, 1)), m)


def peter(m, n):
    if m == 0:
        return n + 1
    if n == 0:
        return peter(m - 1, 1)
    return peter(m - 1, peter(m, n - 1))


# Système F, simulé en Python : entiers de Church polymorphes Nat = ∀α.(α→α)→α→α.
# Les types sont effacés ; seule l'itération intégrée aux entiers est utilisée.
def church(n):
    return lambda f: lambda x: x if n == 0 else f(church(n - 1)(f)(x))


def entier(c):
    return c(lambda k: k + 1)(0)


S_F = lambda n: lambda f: lambda x: f(n(f)(x))          # S : Nat → Nat
UN = church(1)
# H : (Nat→Nat) → Nat → Nat,  H f n = (S n) [Nat] f 1   (f itérée n+1 fois sur 1)
H = lambda f: lambda n: S_F(n)(f)(UN)
# ack : Nat → Nat → Nat,  ack m = m [Nat→Nat] H S   (itération au type Nat→Nat)
ack_F = lambda m: m(H)(S_F)


if __name__ == "__main__":
    P, Q, Rr = 1, 2, 3
    syllogisme = ('imp', ('et', ('tout', 'x', ('imp', ('P', P, 'x'), ('P', Q, 'x'))),
                                ('tout', 'x', ('imp', ('P', Q, 'x'), ('P', Rr, 'x')))),
                  ('tout', 'x', ('imp', ('P', P, 'x'), ('P', Rr, 'x'))))
    deux = ('et', ('ex', 'x', ('P', P, 'x')), ('ex', 'x', ('non', ('P', P, 'x'))))
    faux_ami = ('imp', ('et', ('ex', 'x', ('P', P, 'x')), ('ex', 'x', ('P', Q, 'x'))),
                ('ex', 'x', ('et', ('P', P, 'x'), ('P', Q, 'x'))))
    print("1. logique monadique")
    print("   syllogisme (Barbara) valide :", valide(syllogisme))
    print("   « un P et un non-P » : modèle", satisfaisable(deux), "; valide :", valide(deux))
    print("   « un P et un Q, donc un P et Q » valide :", valide(faux_ami),
          "; contre-modèle :", satisfaisable(('non', faux_ami)))
    print("2. Ackermann dans le Système T")
    ok = all(ack(m)(n) == peter(m, n) for m in range(4) for n in range(5))
    print("   accord avec la définition de Péter pour m < 4, n < 5 :", ok, "; ack(3)(3) =", ack(3)(3))
    print("3. Ackermann dans le Système F (entiers de Church, sans récurseur)")
    okF = all(entier(ack_F(church(m))(church(n))) == peter(m, n) for m in range(4) for n in range(4))
    print("   accord avec Péter pour m < 4, n < 4 :", okF, "; ack 3 3 =", entier(ack_F(church(3))(church(3))))
