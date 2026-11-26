#!/usr/bin/env python3
"""Compilateur : fonctions récursives -> machines de Turing (chapitre « Équivalence » du manuel).

Le programme applique à la lettre la démonstration du théorème « toute fonction récursive est
Turing-calculable ». On fixe une DISCIPLINE DE PILE :
  - la bande contient des blocs de barres séparés par UN blanc : 1^{a1+1} B 1^{a2+1} B ... B 1^{ar+1} ;
  - E désigne la case située deux cases après la dernière barre (là où commencerait un nouveau bloc).
Une machine EMPILE f si, partie de E avec une bande dont les n derniers blocs codent x1..xn,
elle revient en E avec un bloc de plus, qui code f(x1..xn), sans toucher aux blocs précédents
(et ne revient jamais si f(x) n'est pas défini).

On construit, par induction sur le terme, une machine qui empile f, à partir de machines auxiliaires
(les « macros ») : aller_en_E, aller_au_bloc, empiler, copier, decaler, supprimer, incr, decr, zero.
Chaque macro reçoit l'état où elle commence et renvoie l'état où elle finit ; enchaîner deux macros,
c'est donner l'état de sortie de la première comme état d'entrée de la seconde.

Utilisation :
    python3 compilateur.py add 2 3                   compile, exécute, compare à l'évaluation
    python3 compilateur.py "rho[C(0,1), sigma[mult, sigma[S, A(2,1)], A(2,2)]]" 3
    python3 compilateur.py mult 2 3 --sortie mult.tm     écrit la machine dans un fichier
    python3 compilateur.py mult --sortie mult.tm         compile seulement
    python3 machines.py mult.tm 2 3                      l'exécute ensuite, indépendamment

Licence MIT. Frédéric Prost et Claude.
"""
import sys

from machines import Machine, BLANC as B, BARRE as I
from recursives import Const, Succ, Proj, Comp, Rec, Mu, Nomme, lire_terme, evaluer, Diverge, deplier

X = "X"                    # marque auxiliaire utilisée par la copie
SYMBOLES = (B, I, X)


class Assembleur:
    """Accumule des quadruplets et fabrique des noms d'états neufs."""

    def __init__(self, commenter=False):
        self.quads = []
        self.n = 0
        self.commenter = commenter

    def neuf(self, prefixe="s"):
        self.n += 1
        return "%s%d" % (prefixe, self.n)

    def q(self, etat, lu, action, suivant):
        self.quads.append((etat, lu, action, suivant))

    def relier(self, a, b):
        """Passer de l'état a à l'état b sans rien changer : a s s b pour chaque symbole s."""
        for s in SYMBOLES:
            self.q(a, s, s, b)

    # ------------------------------------------------------------ déplacements
    def aller_en_E(self, e):
        """Fin : depuis une case du contenu (barre, X ou séparateur), aller en E.
        On avance jusqu'à trouver deux blancs consécutifs ; la tête s'arrête sur le second."""
        b, s = self.neuf("fin"), self.neuf("fin")
        self.q(e, I, "R", e)
        self.q(e, X, "R", e)
        self.q(e, B, "R", b)
        self.q(b, I, "R", e)
        self.q(b, X, "R", e)
        self.q(b, B, B, s)
        return s

    def aller_au_bloc(self, e, j):
        """Bloc_j : depuis E, aller sur la première barre du j-ième bloc compté depuis la fin."""
        c = self.neuf("bloc")
        self.q(e, B, "L", c)                    # sur le séparateur qui suit le dernier bloc
        for t in range(1, j + 1):
            l = self.neuf("bloc")
            self.q(c, B, "L", l)                # sur la dernière barre du bloc
            self.q(l, I, "L", l)                # on remonte le bloc
            if t < j:
                c = self.neuf("bloc")
                self.q(l, B, B, c)              # séparateur : bloc suivant (vers la gauche)
            else:
                s = self.neuf("bloc")
                self.q(l, B, "R", s)            # on revient sur la première barre
                return s

    # ------------------------------------------------------------ opérations sur la pile
    def empiler(self, e, m):
        """Empiler_m : écrire m+1 barres à partir de E, puis aller au nouvel E."""
        cur = e
        for _ in range(m + 1):
            w, nx = self.neuf("emp"), self.neuf("emp")
            self.q(cur, B, I, w)
            self.q(w, I, "R", nx)
            cur = nx
        s = self.neuf("emp")
        self.q(cur, B, "R", s)
        return s

    def copier(self, e, j):
        """Copier_j : empiler une copie du j-ième bloc depuis la fin.
        Pour chaque barre de la source : la remplacer par X, aller au bout, y écrire une barre,
        revenir jusqu'au X, remettre la barre, passer à la barre suivante."""
        s = self.aller_au_bloc(e, j)
        c1 = self.neuf("cop")
        self.q(s, I, X, c1)                      # première barre marquée
        e1 = self.aller_en_E(c1)
        r = self.neuf("cop")
        self.q(e1, B, I, r)                      # première barre de la copie, écrite en E
        self.q(r, I, "L", r)                     # retour vers la marque
        self.q(r, B, "L", r)
        r1, r2 = self.neuf("cop"), self.neuf("cop")
        self.q(r, X, I, r1)                      # restaurer la barre marquée
        self.q(r1, I, "R", r2)                   # barre suivante de la source
        d = self.neuf("cop")
        self.q(r2, I, X, d)                      # encore une barre : la marquer
        e2 = self.aller_en_E(d)                  # E est deux cases après la copie en cours
        e3 = self.neuf("cop")
        self.q(e2, B, "L", e3)                   # on revient d'une case pour prolonger la copie
        self.q(e3, B, I, r)
        f = self.neuf("cop")
        self.q(r2, B, B, f)                      # fin de la source
        return self.aller_en_E(f)

    def decaler(self, g, k):
        """Décaler_k : la tête est sur un trou (deux blancs) suivi de k blocs ;
        décaler ces k blocs d'une case vers la gauche (on bouche le trou)."""
        cur = g
        for _ in range(k):
            a, b, c, d = self.neuf("dec"), self.neuf("dec"), self.neuf("dec"), self.neuf("dec")
            self.q(cur, B, "R", a)
            self.q(a, B, I, b)                   # écrire une barre dans le trou
            self.q(b, I, "R", b)                 # traverser le bloc
            self.q(b, B, "L", c)
            self.q(c, I, B, d)                   # effacer sa dernière barre : il a reculé d'une case
            cur = d
        s = self.neuf("dec")
        self.q(cur, B, "R", s)
        return s

    def decr(self, e, j):
        """Décr_j : retirer une barre au j-ième bloc (qui code un entier > 0)."""
        s = self.aller_au_bloc(e, j)
        p = self.neuf("decr")
        self.relier(s, p)
        self.q(p, I, "R", p)                     # aller à la dernière barre du bloc
        p2, z = self.neuf("decr"), self.neuf("decr")
        self.q(p, B, "L", p2)
        self.q(p2, I, B, z)                      # l'effacer : un trou de deux blancs apparaît
        return self.decaler(z, j - 1)            # recoller les j-1 blocs qui suivent

    def supprimer(self, e, j):
        """Supprimer_j : supprimer le j-ième bloc depuis la fin, barre par barre, en recollant la suite."""
        boucle = e
        s = self.aller_au_bloc(boucle, j)
        p = self.neuf("sup")
        self.relier(s, p)
        self.q(p, I, "R", p)
        p2, z = self.neuf("sup"), self.neuf("sup")
        self.q(p, B, "L", p2)
        self.q(p2, I, B, z)                      # effacer la dernière barre du bloc
        p4 = self.neuf("sup")
        self.q(z, B, "L", p4)                    # reste-t-il une barre à gauche ?
        z2 = self.neuf("sup")
        self.q(p4, I, "R", z2)                   # oui : revenir, recoller la suite, recommencer
        retour = self.decaler(z2, j - 1)
        self.relier(retour, boucle)
        w = self.neuf("sup")
        self.q(p4, B, B, w)                      # non : le bloc est vide, il reste un trou
        if j == 1:
            s1 = self.neuf("sup")
            self.q(w, B, "R", s1)
            return s1
        z3 = self.neuf("sup")
        self.q(w, B, "R", z3)
        e1 = self.decaler(z3, j - 1)             # premier décalage
        s2 = self.aller_au_bloc(e1, j - 1)       # début du bloc qui suit le trou
        g1, g = self.neuf("sup"), self.neuf("sup")
        self.q(s2, I, "L", g1)
        self.q(g1, B, "L", g)
        return self.decaler(g, j - 1)            # second décalage : le séparateur en trop disparaît

    def incr(self, e):
        """Incr : ajouter une barre au dernier bloc."""
        t, u, v, s = self.neuf("inc"), self.neuf("inc"), self.neuf("inc"), self.neuf("inc")
        self.q(e, B, "L", t)
        self.q(t, B, I, u)
        self.q(u, I, "R", v)
        self.q(v, B, "R", s)
        return s

    def zero(self, e, j):
        """Zéro?_j : renvoie (état si le j-ième bloc code 0, état sinon), tous deux en E."""
        s = self.aller_au_bloc(e, j)
        a, z, nz = self.neuf("zer"), self.neuf("zer"), self.neuf("zer")
        self.q(s, I, "R", a)
        self.q(a, B, B, z)                       # une seule barre : le bloc code 0
        self.q(a, I, I, nz)
        return self.aller_en_E(z), self.aller_en_E(nz)

    # ------------------------------------------------------------ la compilation proprement dite
    def compiler(self, e, f):
        """Machine qui empile f, commençant en e ; renvoie son état de sortie."""
        while isinstance(f, Nomme):
            f = f.terme
        if isinstance(f, Const):                 # m^(k) : Empiler_m
            return self.empiler(e, f.m)
        if isinstance(f, Succ):                  # S : Copier_1 puis Incr
            return self.incr(self.copier(e, 1))
        if isinstance(f, Proj):                  # A^(k)_i : Copier_{k-i+1}
            return self.copier(e, f.k - f.i + 1)
        if isinstance(f, Comp):                  # sigma[g, h1..hk]
            m, k, cur = f.arite(), len(f.hs), e
            for j, h in enumerate(f.hs, start=1):
                for _ in range(m):               # copie des m arguments (y1..y_{j-1} sont au-dessus)
                    cur = self.copier(cur, m + j - 1)
                cur = self.compiler(cur, h)      # empile y_j = h_j(x)
                for _ in range(m):               # supprime les copies, sous y_j
                    cur = self.supprimer(cur, 2)
            cur = self.compiler(cur, f.g)        # empile g(y1..yk)
            for _ in range(k):
                cur = self.supprimer(cur, 2)     # supprime y1..yk
            return cur
        if isinstance(f, Rec):                   # rho[g, h] ; pile : y, x2..xk
            kk, cur = f.arite(), e
            cur = self.copier(cur, kk)           # c := y
            cur = self.empiler(cur, 0)           # i := 0
            for _ in range(kk - 1):
                cur = self.copier(cur, kk + 1)   # copies de x2..xk
            cur = self.compiler(cur, f.g)        # a := g(x)
            for _ in range(kk - 1):
                cur = self.supprimer(cur, 2)
            boucle = cur                         # pile : ..., c, i, a
            fini, continuer = self.zero(boucle, 3)
            fin = self.supprimer(self.supprimer(fini, 3), 2)   # c = 0 : il reste a
            cur = self.decr(continuer, 3)        # c := c - 1
            cur = self.copier(cur, 2)            # i
            cur = self.copier(cur, 2)            # a
            for _ in range(kk - 1):
                cur = self.copier(cur, kk + 4)   # x2..xk
            cur = self.compiler(cur, f.h)        # r := h(i, a, x)
            for _ in range(kk + 1):
                cur = self.supprimer(cur, 2)     # supprime les copies
            cur = self.copier(cur, 3)            # i
            cur = self.incr(cur)                 # i + 1
            cur = self.copier(cur, 2)            # r
            for _ in range(3):
                cur = self.supprimer(cur, 3)     # supprime l'ancien i, l'ancien a, et r en double
            self.relier(cur, boucle)             # retour en tête de boucle
            return fin
        if isinstance(f, Mu):                    # mu[g] ; pile : x1..xn
            n, cur = f.arite(), self.empiler(e, 0)   # z := 0
            boucle = cur
            for _ in range(n + 1):
                cur = self.copier(cur, n + 1)    # copies de x1..xn, z
            cur = self.compiler(cur, f.g)        # r := g(x, z)
            for _ in range(n + 1):
                cur = self.supprimer(cur, 2)
            oui, non = self.zero(cur, 1)
            fin = self.supprimer(oui, 1)         # r = 0 : z est le résultat
            encore = self.incr(self.supprimer(non, 1))   # sinon z := z + 1
            self.relier(encore, boucle)
            return fin
        raise TypeError("terme inconnu : %r" % (f,))


def compiler(f, renommer=True):
    """Machine de Turing Z_f, au format du chapitre 3 : Psi_{Z_f} = f.

    La machine va en E, empile f(x), supprime les n arguments, et retire une barre du résultat
    (il reste alors f(x) barres, la convention de sortie)."""
    a = Assembleur()
    e = a.aller_en_E("q0")
    e = a.compiler(e, f)
    for _ in range(f.arite()):
        e = a.supprimer(e, 2)
    t, u, x = a.neuf("der"), a.neuf("der"), a.neuf("der")
    a.q(e, B, "L", t)
    a.q(t, B, "L", u)
    a.q(u, I, B, x)
    quads = a.quads
    if renommer:                                 # q0, q1, q2... dans l'ordre d'apparition
        noms = {"q0": "q0"}
        for qd in quads:
            for s in (qd[0], qd[3]):
                if s not in noms:
                    noms[s] = "q%d" % len(noms)
        quads = [(noms[a_], s, act, noms[b_]) for a_, s, act, b_ in quads]
    return Machine(quads)


def _principal(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    sortie = None
    if "--sortie" in argv:
        k = argv.index("--sortie")
        sortie = argv[k + 1]
        argv = argv[:k] + argv[k + 2:]
    f = lire_terme(argv[1])
    args = [int(a) for a in argv[2:]]
    m = compiler(f)
    print("terme    :", deplier(f))
    print("machine  : %d quadruplets, %d états" % (len(m), len(m.etats())))
    if sortie:
        with open(sortie, "w", encoding="utf-8") as fh:
            fh.write("# Machine compilée depuis %s\n" % deplier(f))
            fh.write(m.en_texte())
        print("écrite dans", sortie)
    if args or f.arite() == 0:
        c = m.executer(*args, max_pas=10**9)
        print("exécution: %d pas, résultat %d" % (c.pas, c.nombre_de_barres()))
        try:
            print("évaluation directe du terme :", evaluer(f, args))
        except Diverge:
            print("évaluation directe du terme : pas de réponse")
    return 0


if __name__ == "__main__":
    sys.exit(_principal(sys.argv))
