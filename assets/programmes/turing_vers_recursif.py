#!/usr/bin/env python3
"""Traduction : machine de Turing -> fonction récursive (chapitre « Équivalence », sens réciproque).

Pour une machine Z donnée, on construit EXPLICITEMENT un terme f_Z, fait uniquement de constantes,
successeur, projections, substitution, récursion primitive et UNE minimisation, tel que
f_Z(x1..xn) = Psi_Z(x1..xn) (même domaine de définition). C'est la forme normale de Kleene,
avec un codage plus économique que celui des puissances de nombres premiers du manuel
(les deux conviennent : ce qui compte est que chaque étape soit récursive primitive).

Codage d'une configuration (bande, position, état) par UN entier :
  - les symboles sont numérotés 0 (= B), 1 (= barre), 2, ... ; b est le nombre de symboles ;
  - d code la partie droite de la bande, à partir de la case lue, en base b, la case lue étant
    le chiffre des unités : d = s0 + s1·b + s2·b² + ...
  - g code la partie gauche, la case juste à gauche de la tête étant le chiffre des unités ;
  - l'état q_i est codé par son numéro i ;
  - la configuration est le couple de Cantor <g, <i, d>>.
Une bande ne porte qu'un nombre fini de symboles non blancs : g et d sont des entiers.

Les fonctions construites (toutes récursives primitives sauf la dernière) :
  lu(c)          = d mod b                      symbole lu
  etape(c)       = configuration suivante (c elle-même si aucun quadruplet ne s'applique)
  arret(c)       = 1 si aucun quadruplet ne s'applique, 0 sinon
  iter(t, c)     = etape appliquée t fois à c   (récursion primitive sur t)
  init(x1..xn)   = configuration initiale q0 1^{x1+1} B ... B 1^{xn+1}
  barres(t, c)   = nombre de barres de la bande codée par c (en lisant au plus L chiffres)
  temps(x)       = mu t [ arret(iter(t, init(x))) = 1 ]      la seule minimisation
  f_Z(x)         = barres(temps(x), iter(temps(x), init(x)))

Utilisation :
    python3 turing_vers_recursif.py fichier.tm 2 3      construit f_Z, l'évalue, compare à Z
    python3 turing_vers_recursif.py --exemple           sur la machine de l'addition du chapitre 3

Licence MIT. Frédéric Prost et Claude.
"""
import sys

import recursives as r
from recursives import App, fonction, recurrence, minimisation
from machines import Machine, BLANC, BARRE


def somme(termes):
    """Somme écrite comme un arbre équilibré d'additions (profondeur logarithmique)."""
    if len(termes) == 1:
        return termes[0]
    m = len(termes) // 2
    return App(r.add, somme(termes[:m]), somme(termes[m:]))


def cases(conditions_valeurs, defaut):
    """Définition par cas disjoints : somme des [condition]·valeur, plus [aucune condition]·défaut.
    (On pourrait écrire si(c1, v1, si(c2, v2, ...)) ; la somme évite une imbrication trop profonde.)"""
    conds = [c for c, _ in conditions_valeurs]
    aucune = App(r.non, somme(conds)) if conds else 1
    return somme([App(r.mult, c, v) for c, v in conditions_valeurs] + [App(r.mult, aucune, defaut)])


class Traduction:
    """Tous les termes associés à une machine Z."""

    def __init__(self, machine, arite=1):
        self.machine = machine
        self.n = arite
        syms = [BLANC, BARRE] + sorted(machine.symboles() - {BLANC, BARRE})
        etats = [machine.etat_initial] + sorted(machine.etats() - {machine.etat_initial})
        self.sym = {s: k for k, s in enumerate(syms)}
        self.etat = {q: k for k, q in enumerate(etats)}
        self.b = b = len(syms)
        self.symboles, self.etats = syms, etats

        # --- décodage d'une configuration c = <g, <i, d>>
        G = r.gauche
        D = r.droite
        self.cg = fonction(1, lambda c: App(G, c))
        self.ci = fonction(1, lambda c: App(G, App(D, c)))
        self.cd = fonction(1, lambda c: App(D, App(D, c)))
        cg, ci, cd = self.cg, self.ci, self.cd
        self.lu = fonction(1, lambda c: App(r.reste, App(cd, c), b), "lu")
        lu = self.lu

        def conf(g, i, d):
            return App(r.couple, g, App(r.couple, i, d))

        # --- un pas de calcul : définition par cas, un cas par quadruplet
        def nouvelle(c, quad):
            q, s, a, q2 = quad
            i2 = self.etat[q2]
            if a == "R":     # la case lue passe à gauche
                return conf(App(r.add, App(r.mult, App(cg, c), b), App(lu, c)), i2, App(r.quot, App(cd, c), b))
            if a == "L":     # la case à gauche devient la case lue
                return conf(App(r.quot, App(cg, c), b), i2, App(r.add, App(r.mult, App(cd, c), b), App(r.reste, App(cg, c), b)))
            # écriture : le chiffre des unités de d passe de sym[s] à sym[a]
            return conf(App(cg, c), i2, App(r.add, App(r.monus, App(cd, c), self.sym[s]), self.sym[a]))

        def applicable(c, quad):
            return App(r.et, App(r.eg, App(ci, c), self.etat[quad[0]]), App(r.eg, App(lu, c), self.sym[quad[1]]))

        quads = machine.quadruplets
        self.etape = fonction(1, lambda c: cases([(applicable(c, qd), nouvelle(c, qd)) for qd in quads], c), "etape")
        aucun = lambda c: cases([(applicable(c, qd), 0) for qd in quads], 1)
        self.arret = fonction(1, aucun, "arret")
        etape = self.etape
        self.iter = recurrence(2, lambda c: c, lambda t, acc, c: App(etape, acc), "iter")

        # --- configuration initiale : rep(x) = 1 + b + ... + b^x code 1^{x+1}
        self.rep = recurrence(1, lambda: 1, lambda y, acc: App(r.add, App(r.mult, acc, b), 1), "rep")
        rep = self.rep
        n = arite

        def d_init(*xs):
            # d = rep(x1) + b^{x1+2} (rep(x2) + b^{x2+2} ( ... rep(xn)))
            e = App(rep, xs[-1])
            for x in reversed(xs[:-1]):
                e = App(r.add, App(rep, x), App(r.mult, App(r.puiss, b, App(r.add, x, 2)), e))
            return e
        self.init = fonction(n, lambda *xs: conf(0, 0, d_init(*xs)), "init")

        # --- lecture du résultat : compter les chiffres égaux à 1 (au plus L chiffres)
        # chiffres(L, m) = couple(m', nb) après L tours de : m' := m' div b ; nb := nb + [m' mod b = 1]
        un = self.sym[BARRE]
        self.compte = recurrence(2, lambda m: App(r.couple, m, 0),
                                 lambda k, p, m: App(r.couple, App(r.quot, App(r.gauche, p), b),
                                                     App(r.add, App(r.droite, p), App(r.eg, App(r.reste, App(r.gauche, p), b), un))),
                                 "compte")
        compte = self.compte
        nb = lambda L, m: App(r.droite, App(compte, L, m))
        # longueur utile : t + somme des (x_i + 2) majore le nombre de cases visitées
        self.barres = fonction(n + 2, lambda t, c, *xs: App(r.add, nb(self.longueur(t, xs), App(cg, c)), nb(self.longueur(t, xs), App(cd, c))), "barres")

        init, iter_, arret = self.init, self.iter, self.arret
        self.temps = minimisation(n, lambda *a: App(r.non, App(arret, App(iter_, a[-1], App(init, *a[:-1])))), "temps")
        temps = self.temps
        self.f = fonction(n, lambda *xs: App(self.barres, App(temps, *xs), App(iter_, App(temps, *xs), App(init, *xs)), *xs), "f_Z")

    def longueur(self, t, xs):
        e = t
        for x in xs:
            e = App(r.add, e, App(r.add, x, 2))
        return e

    def code_configuration(self, conf):
        """Code <g, <i, d>> d'une configuration du simulateur (pour vérifier pas à pas)."""
        b, p = self.b, conf.position
        d = g = 0
        cles = [k for k, v in conf.bande.items() if v != BLANC]
        hi = max(cles + [p])
        lo = min(cles + [p])
        for k in range(hi, p - 1, -1):
            d = d * b + self.sym[conf.bande.get(k, BLANC)]
        for k in range(lo, p):
            g = g * b + self.sym[conf.bande.get(k, BLANC)]
        return r.cantor(g, r.cantor(self.etat[conf.etat], d))


def verifier(machine, args, rapide=True, max_pas=2000):
    """Vérifie, pas à pas, que etape suit exactement le simulateur, puis évalue f_Z."""
    T = Traduction(machine, len(args))
    c = machine.configuration_initiale(*args)
    code = r.evaluer(T.init, args, rapide)
    assert code == T.code_configuration(c), "configuration initiale"
    while machine.pas(c):
        code = r.evaluer(T.etape, (code,), rapide)
        assert code == T.code_configuration(c), "pas %d" % c.pas
        if c.pas > max_pas:
            raise RuntimeError("trop long pour une vérification")
    assert r.evaluer(T.arret, (code,), rapide) == 1
    return T, r.evaluer(T.f, args, rapide), c.nombre_de_barres()


ADDITION = """q0 1 B q1
q1 B R q2
q2 1 R q2
q2 B R q3
q3 1 B q4"""


def _principal(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    if argv[1] == "--exemple":
        m, args = Machine.depuis_texte(ADDITION), [2, 3]
    else:
        m, args = Machine.depuis_fichier(argv[1]), [int(a) for a in argv[2:]]
    T, v, attendu = verifier(m, args)
    print("machine          : %d quadruplets, %d symboles, %d états" % (len(m), T.b, len(T.etats)))
    print("terme f_Z        : %d briques (entièrement déplié)" % r.taille(T.f))
    print("  dont etape     : %d briques ; minimisations : 1" % r.taille(T.etape))
    print("etape suit le simulateur pas à pas : oui")
    print("f_Z%s = %d   (la machine donne %d)" % (tuple(args), v, attendu))
    return 0


if __name__ == "__main__":
    sys.exit(_principal(sys.argv))
