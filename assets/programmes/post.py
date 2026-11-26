"""post.py : le problème de correspondance de Post, et la traduction d'une machine de Turing en dominos.

Un domino est un couple (haut, bas) de mots ; ici un mot est un tuple de « lettres », chaque lettre
étant une chaîne (un symbole de la bande, un nom d'état, le séparateur #...). Une solution d'une liste
de dominos est une suite d'indices telle que la concaténation des hauts égale celle des bas.

Construction (chapitre « Autres modèles ») : pour une machine Z et une entrée x, on fabrique
 1. une liste de dominos « modifiée », dont la solution doit commencer par le premier domino ;
    elle a une solution si et seulement si Z s'arrête sur x : la seule façon d'égaliser le haut et le
    bas est d'écrire la suite des configurations du calcul, séparées par #, le bas ayant toujours une
    configuration d'avance ;
 2. une liste de dominos ordinaire, par l'astuce des étoiles du chapitre « Langages ».

    python3 post.py                         # dominos pour l'addition 1 + 1, solution vérifiée
    python3 post.py exemples/successeur.tm 0 --dominos
    python3 post.py --chercher              # recherche en largeur sur de petits exemples

Licence MIT. Auteurs : Frédéric Prost et Claude.
"""
import sys
from collections import deque

from machines import Machine, BLANC, bande_initiale

SEP, ARRET, ETOILE, FIN = "#", "H", "⋆", "◇"


# --------------------------------------------------------------------------- solutions
def concatener(dominos, indices):
    haut, bas = [], []
    for i in indices:
        haut.extend(dominos[i][0])
        bas.extend(dominos[i][1])
    return tuple(haut), tuple(bas)


def est_solution(dominos, indices, premier=None):
    if not indices or (premier is not None and indices[0] != premier):
        return False
    h, b = concatener(dominos, indices)
    return h == b


def chercher(dominos, max_noeuds=200000, premier=None):
    """Recherche en largeur d'une solution. On ne garde que l'« avance » d'un côté sur l'autre :
    deux suites qui laissent la même avance ont les mêmes prolongements. Renvoie une solution
    (liste d'indices) ou None si rien n'est trouvé dans la limite : c'est une semi-décision."""
    depart = [premier] if premier is not None else range(len(dominos))
    file, vus = deque(), set()

    def avance(h, b):
        n = min(len(h), len(b))
        if h[:n] != b[:n]:
            return None
        return ("h", h[n:]) if len(h) > n else ("b", b[n:])

    for i in depart:
        a = avance(*dominos[i])
        if a is not None:
            if a[1] == ():
                return [i]
            file.append((a, [i]))
            vus.add(a)
    while file and len(vus) < max_noeuds:
        (cote, reste), suite = file.popleft()
        for i, (h, b) in enumerate(dominos):
            if cote == "h":
                a = avance(reste + h, b)
            else:
                a = avance(h, reste + b)
            if a is None:
                continue
            if a[1] == ():
                return suite + [i]
            if a not in vus:
                vus.add(a)
                file.append((a, suite + [i]))
    return None


# --------------------------------------------------------------------------- machine -> dominos
def dominos_modifies(machine, *args):
    """Liste de dominos dont une solution commençant par le domino 0 existe ssi la machine s'arrête.
    Renvoie (dominos, noms) où noms[i] explique le rôle du domino i."""
    sigma = sorted(machine.symboles())
    etats = sorted(machine.etats())
    bande = bande_initiale(args)
    mot = tuple(bande.get(i, BLANC) for i in range(max(bande) + 1)) if bande else (BLANC,)
    D, noms = [], []

    def ajoute(h, b, nom):
        D.append((tuple(h), tuple(b)))
        noms.append(nom)

    # départ : la première configuration, précédée d'un blanc (inoffensif) pour pouvoir aller à gauche
    ajoute([SEP], [SEP, BLANC, machine.etat_initial] + list(mot) + [SEP], "départ")
    for a in sigma:
        ajoute([a], [a], "copie " + a)
    ajoute([SEP], [SEP], "séparateur")
    ajoute([SEP], [BLANC, SEP], "séparateur, un blanc ajouté à droite")
    for (q, s, act, q2) in machine.quadruplets:
        nom = "règle %s %s %s %s" % (q, s, act, q2)
        if act == "R":
            ajoute([q, s], [s, q2], nom)
        elif act == "L":
            for c in sigma:
                ajoute([c, q, s], [q2, c, s], nom)
            ajoute([SEP, q, s], [SEP, q2, BLANC, s], nom + " (bord gauche)")
            ajoute([SEP, q, s], [BLANC, SEP, q2, BLANC, s], nom + " (bord gauche, blanc à droite)")
        else:
            ajoute([q, s], [q2, act], nom)
    for q in etats:
        for s in sigma:
            if (q, s) not in machine.table:
                ajoute([q, s], [ARRET, s], "arrêt en %s sur %s" % (q, s))
    for a in sigma:
        ajoute([a, ARRET], [ARRET], "effacement à gauche de H")
        ajoute([ARRET, a], [ARRET], "effacement à droite de H")
    ajoute([ARRET, SEP, SEP], [SEP], "fin")
    return D, noms


def solution_depuis_calcul(machine, dominos, noms, *args, max_pas=10**5):
    """Construit la solution du problème modifié à partir du calcul de la machine (qui doit s'arrêter).
    On écrit les lignes successives (les configurations) ; chaque ligne du haut est recopiée en bas
    en la transformant en la ligne suivante, le bas ayant toujours une ligne d'avance."""
    index = {}
    for i, (h, b) in enumerate(dominos):
        index.setdefault((tuple(h), tuple(b)), i)

    def ind(h, b):
        return index[(tuple(h), tuple(b))]

    def copie(mots):
        return [ind([c], [c]) for c in mots]

    bande = bande_initiale(args)
    droite = [bande.get(i, BLANC) for i in range(max(bande) + 1)] if bande else [BLANC]
    gauche, q = [BLANC], machine.etat_initial
    sol = [0]
    pad = False                 # faut-il ajouter un blanc à droite de la ligne suivante ?
    premiere, pas = True, 0
    while True:
        s = droite[0]
        regle = machine.table.get((q, s))
        bord_gauche = regle is not None and regle[2] == "L" and not gauche
        # le séparateur du haut qui précède cette ligne écrit, en bas, la fin de la ligne suivante
        if not premiere and not bord_gauche:
            sol.append(ind([SEP], ([BLANC] if pad else []) + [SEP]))
        if regle is None:                                         # la machine s'arrête
            sol += copie(gauche) + [ind([q, s], [ARRET, s])] + copie(droite[1:])
            break
        act, q2 = regle[2], regle[3]
        ancien_pad, pad = pad, False
        if act == "R":
            sol += copie(gauche) + [ind([q, s], [s, q2])] + copie(droite[1:])
            gauche, droite = gauche + [s], droite[1:]
            if not droite:
                droite, pad = [BLANC], True
        elif act == "L" and bord_gauche:
            sol.append(ind([SEP, q, s], ([BLANC] if ancien_pad else []) + [SEP, q2, BLANC, s]))
            sol += copie(droite[1:])
            droite = [BLANC] + droite
        elif act == "L":
            c = gauche[-1]
            sol += copie(gauche[:-1]) + [ind([c, q, s], [q2, c, s])] + copie(droite[1:])
            gauche, droite = gauche[:-1], [c] + droite
        else:
            sol += copie(gauche) + [ind([q, s], [q2, act])] + copie(droite[1:])
            droite = [act] + droite[1:]
        q, premiere, pas = q2, False, pas + 1
        if pas > max_pas:
            raise RuntimeError("trop long")
    # la ligne du bas contient maintenant H ; on efface une lettre par ligne
    ligne = gauche + [ARRET] + droite
    while len(ligne) > 1:
        sol.append(ind([SEP], ([BLANC] if pad else []) + [SEP]))
        if pad:
            ligne = ligne + [BLANC]
            pad = False
        k = ligne.index(ARRET)
        if k > 0:
            sol += copie(ligne[:k - 1]) + [ind([ligne[k - 1], ARRET], [ARRET])] + copie(ligne[k + 1:])
            ligne = ligne[:k - 1] + ligne[k:]
        else:
            sol += [ind([ARRET, ligne[1]], [ARRET])] + copie(ligne[2:])
            ligne = [ARRET] + ligne[2:]
    sol.append(ind([SEP], [SEP]))
    sol.append(ind([ARRET, SEP, SEP], [SEP]))
    return sol


def vers_ordinaire(dominos):
    """Astuce des étoiles (chapitre « Langages ») : le premier domino devient le seul qui puisse commencer."""
    def gauche(w):
        r = []
        for c in w:
            r += [ETOILE, c]
        return r

    def droite(w):
        r = []
        for c in w:
            r += [c, ETOILE]
        return r
    nouveaux = [(tuple(gauche(dominos[0][0])), tuple([ETOILE] + droite(dominos[0][1])))]
    for h, b in dominos:
        nouveaux.append((tuple(gauche(h)), tuple(droite(b))))
    nouveaux.append(((ETOILE, FIN), (FIN,)))
    return nouveaux


def solution_ordinaire(sol_modifiee, nb_dominos):
    """Une solution 0, i2, ..., ir du problème modifié donne la solution 0, i2+1, ..., ir+1, fin."""
    return [0] + [i + 1 for i in sol_modifiee[1:]] + [nb_dominos + 1]


def afficher_mot(w, max_lettres=60):
    t = " ".join(w)
    return t if len(w) <= max_lettres else " ".join(w[:max_lettres]) + " …"


def _principal(argv):
    import os
    if "--chercher" in argv:
        exemples = [
            [(("a",), ("b", "a", "a")), (("a", "b"), ("a", "a")), (("b", "b", "a"), ("b", "b"))],
            [(("1",), ("1", "1", "1")), (("1", "0", "1", "1", "1"), ("1", "0")), (("1", "0"), ("0",))],
            [(("a", "b"), ("a",)), (("b",), ("a", "b"))],
        ]
        for d in exemples:
            s = chercher(d)
            print(" / ".join("%s:%s" % ("".join(h), "".join(b)) for h, b in d), "->", s)
        m = Machine.depuis_texte("q0 1 B q1")
        dm, _ = dominos_modifies(m, 0)
        print("Machine « q0 1 B q1 » sur 0 :", len(dm), "dominos ; solution trouvée par la recherche :", chercher(dm, premier=0))
        return
    voir = "--dominos" in argv
    argv = [a for a in argv if not a.startswith("--")]
    if len(argv) >= 2:
        machine = Machine.depuis_fichier(argv[1])
        args = [int(x) for x in argv[2:]]
    else:
        machine = Machine.depuis_fichier(os.path.join(os.path.dirname(os.path.abspath(__file__)), "exemples", "addition.tm"))
        args = [1, 1]
    dm, noms = dominos_modifies(machine, *args)
    if voir:
        for i, ((h, b), n) in enumerate(zip(dm, noms)):
            print("%3d  %-22s / %-28s %s" % (i, " ".join(h), " ".join(b), n))
    sol = solution_depuis_calcul(machine, dm, noms, *args)
    assert est_solution(dm, sol, premier=0)
    h, _ = concatener(dm, sol)
    print("Problème modifié : %d dominos ; solution de %d dominos, vérifiée." % (len(dm), len(sol)))
    print("Mot commun :", afficher_mot(h, 80))
    do = vers_ordinaire(dm)
    so = solution_ordinaire(sol, len(dm))
    assert est_solution(do, so)
    print("Problème de Post ordinaire : %d dominos ; solution de %d dominos, vérifiée." % (len(do), len(so)))


if __name__ == "__main__":
    _principal(sys.argv)
