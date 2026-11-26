"""piles.py : automates à deux piles, et traduction d'une machine de Turing en automate à deux piles.

Un automate à deux piles a un ensemble fini d'états et deux piles G (gauche) et D (droite).
À chaque pas, il regarde son état et les sommets des deux piles (VIDE si une pile est vide),
puis il peut dépiler chacune des deux piles, empiler un mot sur chacune, et changer d'état.
S'il n'a pas de transition pour ce qu'il voit, il s'arrête.

Simulation d'une bande (chapitre « Autres modèles ») : la pile D contient la case lue (au sommet)
et toutes les cases à sa droite ; la pile G contient les cases à gauche de la tête, la plus proche
au sommet. Une pile vide se lit comme une infinité de blancs.

    python3 piles.py                    # traduit l'addition et compare les deux exécutions
    python3 piles.py exemples/addition.tm 2 3 --trace

Licence MIT. Auteurs : Frédéric Prost et Claude.
"""
import sys

from machines import Machine, BLANC, BARRE, bande_initiale

VIDE = "⊥"


class AutomateDeuxPiles:
    """Transitions : (état, sommet de G, sommet de D) -> (dépiler G, dépiler D, mot empilé sur G,
    mot empilé sur D, nouvel état). Les mots empilés sont des tuples, le dernier élément au sommet."""

    def __init__(self, transitions, etat_initial):
        self.transitions = dict(transitions)
        self.etat_initial = etat_initial

    def __len__(self):
        return len(self.transitions)

    def pas(self, etat, G, D):
        """Effectue un pas (G et D sont des listes, sommet à la fin). Renvoie le nouvel état, ou None à l'arrêt."""
        cle = (etat, G[-1] if G else VIDE, D[-1] if D else VIDE)
        t = self.transitions.get(cle)
        if t is None:
            return None
        dep_g, dep_d, emp_g, emp_d, suivant = t
        if dep_g:
            G.pop()
        if dep_d:
            D.pop()
        G.extend(emp_g)
        D.extend(emp_d)
        return suivant

    def executer(self, G, D, max_pas=10**7, trace=None):
        etat, n = self.etat_initial, 0
        while True:
            if trace:
                trace(etat, G, D)
            nouveau = self.pas(etat, G, D)
            if nouveau is None:
                return etat, G, D, n
            etat, n = nouveau, n + 1
            if n >= max_pas:
                raise RuntimeError("pas d'arrêt après %d pas" % n)


def depuis_turing(machine):
    """Traduit une machine de Turing à quadruplets en automate à deux piles qui fait un pas
    pour chaque pas de la machine. Le blanc n'est jamais empilé inutilement : une pile vide vaut des blancs."""
    sommets = sorted(machine.symboles()) + [VIDE]
    trans = {}
    for (q, s, action, q2) in machine.quadruplets:
        lus_d = [s, VIDE] if s == BLANC else [s]          # sur D, un blanc peut être une pile vide
        for d in lus_d:
            depile_d = d != VIDE
            for g in sommets:
                if action == "R":
                    # la case lue passe sur G ; la case suivante devient le sommet de D
                    emp_g = () if (s == BLANC and g == VIDE) else (s,)
                    trans[(q, g, d)] = (False, depile_d, emp_g, (), q2)
                elif action == "L":
                    # le sommet de G (ou un blanc) revient sur D, au-dessus de la case lue
                    emp_d = ((s,) if depile_d or s != BLANC else ()) + (g if g != VIDE else BLANC,)
                    trans[(q, g, d)] = (g != VIDE, depile_d, (), emp_d, q2)
                else:
                    # écrire : on remplace le sommet de D
                    trans[(q, g, d)] = (False, depile_d, (), (action,), q2)
    return AutomateDeuxPiles(trans, machine.etat_initial)


def piles_initiales(*args):
    """La bande initiale q0 1^{x1+1} B ... : G vide, D contient la bande, la première case au sommet."""
    bande = bande_initiale(args)
    n = max(bande) + 1 if bande else 0
    return [], [bande.get(i, BLANC) for i in reversed(range(n))]


def bande_depuis_piles(G, D):
    """Reconstitue (dictionnaire des cases non blanches, position de la tête = 0)."""
    bande = {}
    for i, s in enumerate(reversed(D)):
        if s != BLANC:
            bande[i] = s
    for i, s in enumerate(reversed(G)):
        if s != BLANC:
            bande[-1 - i] = s
    return bande


def comparer(machine, *args, max_pas=10**6):
    """Exécute la machine et l'automate côte à côte et vérifie, pas à pas, que la bande et l'état
    sont les mêmes. Renvoie (nombre de pas, nombre de barres)."""
    auto = depuis_turing(machine)
    c = machine.configuration_initiale(*args)
    G, D = piles_initiales(*args)
    etat = auto.etat_initial
    while True:
        bande = {i - c.position: s for i, s in c.bande.items() if s != BLANC}
        assert bande == bande_depuis_piles(G, D), "bandes différentes au pas %d" % c.pas
        assert etat == c.etat
        continue_m = machine.pas(c)
        nouveau = auto.pas(etat, G, D)
        assert (nouveau is None) == (not continue_m), "arrêts différents au pas %d" % c.pas
        if nouveau is None:
            return c.pas, c.nombre_de_barres()
        etat = nouveau
        if c.pas > max_pas:
            raise RuntimeError("trop long")


def afficher(etat, G, D):
    gauche = " ".join(G) if G else ""
    droite = " ".join(reversed(D)) if D else ""
    print("  %-6s G = [%s|   |%s] = D" % (etat, gauche, droite))


def _principal(argv):
    trace = "--trace" in argv
    argv = [a for a in argv if a != "--trace"]
    if len(argv) >= 2:
        machine = Machine.depuis_fichier(argv[1])
        args = [int(a) for a in argv[2:]]
    else:
        import os
        machine = Machine.depuis_fichier(os.path.join(os.path.dirname(os.path.abspath(__file__)), "exemples", "addition.tm"))
        args = [2, 3]
    auto = depuis_turing(machine)
    print("Machine de Turing : %d quadruplets ; automate à deux piles : %d transitions." % (len(machine), len(auto)))
    if trace:
        G, D = piles_initiales(*args)
        auto.executer(G, D, trace=afficher)
    pas, barres = comparer(machine, *args)
    print("Entrée %s : les deux exécutions coïncident pendant %d pas ; résultat %d barres, soit %d." % (args, pas, barres, barres))


if __name__ == "__main__":
    _principal(sys.argv)
