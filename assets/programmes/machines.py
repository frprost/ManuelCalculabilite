#!/usr/bin/env python3
"""Machines de Turing à quadruplets (présentation de M. Davis, chapitre 3 du manuel).

Un quadruplet (q, s, a, q2) se lit : « dans l'état q, si la tête lit le symbole s,
faire l'action a puis passer dans l'état q2 ». L'action a est
  - un symbole (on l'écrit dans la case lue),
  - 'L' (la tête va d'une case à gauche) ou 'R' (d'une case à droite).
La machine s'arrête quand aucun quadruplet ne commence par (état courant, symbole lu).

Conventions d'entrée et de sortie (celles du manuel) :
  - l'entier x est écrit sur la bande comme x+1 barres « 1 » ;
  - les arguments sont séparés par un blanc B ;
  - la machine démarre dans l'état q0, la tête sur la première barre ;
  - le résultat est le nombre total de barres présentes à l'arrêt.

Utilisation en ligne de commande :
    python3 machines.py fichier.tm 2 3          exécute la machine sur (2, 3)
    python3 machines.py fichier.tm 2 3 --trace  affiche chaque description instantanée
Un fichier .tm contient un quadruplet par ligne, par exemple « q0 1 B q1 » ;
ce qui suit un « # » est un commentaire.

Licence MIT. Frédéric Prost et Claude.
"""
import sys

BLANC = "B"
BARRE = "1"


class MachineNonConsistante(ValueError):
    """Deux quadruplets commencent par le même couple (état, symbole)."""


class Machine:
    """Une machine de Turing à quadruplets.

    >>> m = Machine.depuis_texte("q0 1 B q1\\nq1 B R q2\\nq2 1 R q2\\nq2 B R q3\\nq3 1 B q4")
    >>> m.calculer(2, 3)
    5
    """

    def __init__(self, quadruplets, etat_initial="q0"):
        self.quadruplets = [tuple(q) for q in quadruplets]
        self.etat_initial = etat_initial
        self.table = {}
        for q in self.quadruplets:
            if len(q) != 4:
                raise ValueError("quadruplet mal formé : %r" % (q,))
            cle = (q[0], q[1])
            if cle in self.table and self.table[cle] != q:
                raise MachineNonConsistante("deux quadruplets commencent par %s %s" % cle)
            self.table[cle] = q

    # ---------------------------------------------------------------- lecture
    @classmethod
    def depuis_texte(cls, texte, etat_initial="q0"):
        """Lit des quadruplets, un par ligne (ou séparés par « ; »)."""
        quads = []
        for ligne in texte.replace(";", "\n").splitlines():
            ligne = ligne.split("#", 1)[0].replace("(", " ").replace(")", " ").replace(",", " ").strip()
            if ligne:
                morceaux = ligne.split()
                if len(morceaux) != 4:
                    raise ValueError("quadruplet mal formé : « %s »" % ligne)
                quads.append(tuple(morceaux))
        return cls(quads, etat_initial)

    @classmethod
    def depuis_fichier(cls, chemin):
        with open(chemin, encoding="utf-8") as f:
            return cls.depuis_texte(f.read())

    def en_texte(self):
        return "\n".join(" ".join(q) for q in self.quadruplets) + "\n"

    def etats(self):
        e = {self.etat_initial}
        for q in self.quadruplets:
            e.add(q[0])
            e.add(q[3])
        return e

    def symboles(self):
        s = {BLANC, BARRE}
        for q in self.quadruplets:
            s.add(q[1])
            if q[2] not in ("L", "R"):
                s.add(q[2])
        return s

    def __len__(self):
        return len(self.quadruplets)

    # ---------------------------------------------------------------- exécution
    def configuration_initiale(self, *args):
        return Configuration(bande_initiale(args), 0, self.etat_initial)

    def pas(self, c):
        """Effectue un pas sur la configuration c (modifiée sur place).
        Renvoie False si la machine est arrêtée."""
        lu = c.bande.get(c.position, BLANC)
        q = self.table.get((c.etat, lu))
        if q is None:
            return False
        action = q[2]
        if action == "L":
            c.position -= 1
        elif action == "R":
            c.position += 1
        elif action == BLANC:
            c.bande.pop(c.position, None)
        else:
            c.bande[c.position] = action
        c.etat = q[3]
        c.pas += 1
        return True

    def executer(self, *args, max_pas=10**8, trace=None):
        """Exécute la machine. Renvoie la configuration finale.
        Lève TempsDepasse si la machine ne s'est pas arrêtée après max_pas pas."""
        c = self.configuration_initiale(*args)
        if trace is not None:
            trace(c)
        while self.pas(c):
            if trace is not None:
                trace(c)
            if c.pas >= max_pas:
                raise TempsDepasse(c)
        return c

    def calculer(self, *args, max_pas=10**8):
        """Valeur Psi_Z(args) : le nombre de barres à l'arrêt."""
        return self.executer(*args, max_pas=max_pas).nombre_de_barres()

    def calcul_complet(self, *args, max_pas=10**6):
        """La liste des descriptions instantanées du calcul (le « calcul » au sens du chapitre 3)."""
        lignes = []
        self.executer(*args, max_pas=max_pas, trace=lambda c: lignes.append(c.description()))
        return lignes


class TempsDepasse(RuntimeError):
    def __init__(self, configuration):
        super().__init__("pas d'arrêt après %d pas" % configuration.pas)
        self.configuration = configuration


def bande_initiale(args):
    """Bande q0 1^{x1+1} B 1^{x2+1} B ... sous forme de dictionnaire {position: symbole}."""
    bande, pos = {}, 0
    for j, x in enumerate(args):
        if j > 0:
            pos += 1
        for _ in range(x + 1):
            bande[pos] = BARRE
            pos += 1
    return bande


class Configuration:
    """Bande (dictionnaire des cases non blanches), position de la tête, état, nombre de pas."""

    def __init__(self, bande, position, etat):
        self.bande, self.position, self.etat, self.pas = dict(bande), position, etat, 0

    def nombre_de_barres(self):
        return sum(1 for s in self.bande.values() if s == BARRE)

    def description(self):
        """Description instantanée « γ q S δ » : l'état est écrit juste avant la case lue."""
        cles = list(self.bande) + [self.position]
        lo, hi = min(cles), max(cles)
        mots = []
        for i in range(lo, hi + 1):
            if i == self.position:
                mots.append(self.etat)
            mots.append(self.bande.get(i, BLANC))
        return " ".join(mots)


def quintuplets_vers_quadruplets(quintuplets):
    """Traduit une machine à quintuplets (q, s, écrit, déplacement L/R, q2) en machine à quadruplets :
    chaque quintuplet devient deux quadruplets, par un état intermédiaire neuf (chapitre 3, variantes)."""
    quads, k = [], 0
    for q, s, ecrit, dep, q2 in quintuplets:
        k += 1
        mid = "%s_%s_%d" % (q, s, k)
        quads.append((q, s, ecrit, mid))
        # dans l'état intermédiaire, le symbole lu est forcément celui qu'on vient d'écrire
        quads.append((mid, ecrit, dep, q2))
    return Machine(quads, quintuplets[0][0] if quintuplets else "q0")


def _principal(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    m = Machine.depuis_fichier(argv[1])
    trace = "--trace" in argv
    args = [int(a) for a in argv[2:] if not a.startswith("--")]
    if trace:
        for ligne in m.calcul_complet(*args):
            print(ligne)
    c = m.executer(*args)
    print("arrêt après %d pas, %d barres : résultat %d" % (c.pas, c.nombre_de_barres(), c.nombre_de_barres()))
    return 0


if __name__ == "__main__":
    sys.exit(_principal(sys.argv))
