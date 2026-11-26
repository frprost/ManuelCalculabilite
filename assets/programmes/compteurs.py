"""compteurs.py : machines à compteurs, et traduction d'une machine de Turing en machine à deux compteurs.

Une machine à compteurs a des compteurs (des entiers naturels) et un programme numéroté :
    ("INC", r, j)      ajouter 1 au compteur r, aller à l'instruction j ;
    ("DEC", r, j, k)   si r > 0, retirer 1 et aller en j ; sinon aller en k ;
    ("STOP",)          s'arrêter.

La traduction se fait en deux étapes (chapitre « Autres modèles ») :

 1. Machine de Turing -> trois compteurs g, d, t. La bande est vue comme deux nombres écrits
    en base b (b = nombre de symboles, le blanc valant le chiffre 0) : d contient la case lue
    (chiffre des unités) et les cases à sa droite, g les cases à gauche de la tête (la plus proche
    aux unités). Lire la case, c'est calculer le reste de d par b ; aller à droite, c'est retirer
    ce chiffre de d et l'ajouter à g ; t est un compteur auxiliaire pour multiplier et diviser par b.
 2. Trois compteurs -> deux compteurs A, B : on range (g, d, t) dans le seul nombre 2^g 3^d 5^t
    (compteur A), B servant d'auxiliaire ; INC et DEC deviennent des multiplications et des divisions.

Une machine à deux compteurs fait un nombre astronomique de pas (chaque INC de l'étape 1 multiplie A
par 3, une instruction après l'autre). L'interpréteur ci-dessous exécute donc les petites boucles
d'un seul coup (« accélération ») : le résultat est exactement celui de l'exécution pas à pas, et le
nombre de pas affiché est le vrai nombre de pas de la machine.

    python3 compteurs.py                     # addition 2 + 1, sur trois puis sur deux compteurs
    python3 compteurs.py exemples/successeur.tm 4

Licence MIT. Auteurs : Frédéric Prost et Claude.
"""
import sys

from machines import Machine, BLANC, BARRE, bande_initiale


# --------------------------------------------------------------------------- interpréteur
class MachineCompteurs:
    def __init__(self, programme, compteurs):
        self.programme = programme
        self.compteurs = list(compteurs)
        self._cycles = {}

    def __len__(self):
        return len(self.programme)

    def _cycle(self, i):
        """Si l'instruction i = DEC(X, ...) commence une boucle « simple » (en suivant les succès :
        uniquement des DEC du même compteur X et des INC d'autres compteurs, retour en i),
        renvoie (nombre de DEC par tour, variations des autres compteurs, longueur du tour)."""
        if i in self._cycles:
            return self._cycles[i]
        X = self.programme[i][1]
        j, ndec, delta, longueur, res = i, 0, {}, 0, None
        for _ in range(200):
            ins = self.programme[j]
            longueur += 1
            if ins[0] == "DEC" and ins[1] == X:
                ndec += 1
                j = ins[2]
            elif ins[0] == "INC" and ins[1] != X:
                delta[ins[1]] = delta.get(ins[1], 0) + 1
                j = ins[2]
            else:
                break
            if j == i:
                res = (ndec, delta, longueur)
                break
        self._cycles[i] = res
        return res

    def executer(self, valeurs, max_pas_reels=10**7, accelerer=True):
        """Renvoie (valeurs finales, nombre de pas de la machine, nombre d'itérations de l'interpréteur)."""
        v = list(valeurs)
        i, pas, iterations = 0, 0, 0
        while True:
            iterations += 1
            if iterations > max_pas_reels:
                raise RuntimeError("trop long")
            ins = self.programme[i]
            if ins[0] == "STOP":
                return v, pas, iterations
            if ins[0] == "INC":
                v[ins[1]] += 1
                i = ins[2]
                pas += 1
                continue
            X = ins[1]
            if accelerer:
                cyc = self._cycle(i)
                if cyc is not None and v[X] >= cyc[0]:
                    tours = v[X] // cyc[0]
                    v[X] -= tours * cyc[0]
                    for r, dv in cyc[1].items():
                        v[r] += tours * dv
                    pas += tours * cyc[2]
                    continue
            if v[X] > 0:
                v[X] -= 1
                i = ins[2]
            else:
                i = ins[3]
            pas += 1


class Assembleur:
    """Écrit un programme à étiquettes : chaque instruction reçoit un numéro, les sauts sont résolus à la fin."""

    def __init__(self):
        self.code, self.etiquettes, self.n = [], {}, 0

    def neuf(self, prefixe="e"):
        self.n += 1
        return "%s%d" % (prefixe, self.n)

    def ici(self, etiquette):
        self.etiquettes[etiquette] = len(self.code)

    def inc(self, r, suivant):
        self.code.append(["INC", r, suivant])

    def dec(self, r, si_oui, si_non):
        self.code.append(["DEC", r, si_oui, si_non])

    def stop(self):
        self.code.append(["STOP"])

    def assembler(self):
        def res(x):
            return self.etiquettes[x] if isinstance(x, str) else x
        prog = []
        for ins in self.code:
            if ins[0] == "INC":
                prog.append(("INC", ins[1], res(ins[2])))
            elif ins[0] == "DEC":
                prog.append(("DEC", ins[1], res(ins[2]), res(ins[3])))
            else:
                prog.append(("STOP",))
        return prog

    # ---- fragments : chacun commence à l'étiquette donnée et saute à « fin »
    def transferer(self, src, dst, facteur, debut, fin):
        """dst += facteur * src ; src := 0."""
        self.ici(debut)
        corps = [self.neuf() for _ in range(facteur)]
        self.dec(src, corps[0] if facteur else debut, fin)
        for k, e in enumerate(corps):
            self.ici(e)
            self.inc(dst, corps[k + 1] if k + 1 < facteur else debut)

    def ajouter(self, r, n, debut, fin):
        """r += n (n constant)."""
        if n == 0:
            self.ici(debut)
            self.dec_nulle(fin)
            return
        etiq = [debut] + [self.neuf() for _ in range(n - 1)] + [fin]
        for k in range(n):
            self.ici(etiq[k])
            self.inc(r, etiq[k + 1])

    def dec_nulle(self, fin):
        # « aller en fin » : on simule un saut par une instruction sur un compteur réservé, toujours nul
        self.dec(Z, fin, fin)

    def diviser(self, src, quot, b, debut, sorties):
        """quot += src // b ; src := 0 ; saute à sorties[reste]."""
        etapes = [debut] + [self.neuf() for _ in range(b)]
        for k in range(b):
            self.ici(etapes[k])
            self.dec(src, etapes[k + 1], sorties[k])
        self.ici(etapes[b])
        self.inc(quot, debut)


G, D, T, Z = 0, 1, 2, 3          # compteurs de l'étape 1 (Z : compteur toujours nul, pour les sauts)


def codes_symboles(machine):
    """Le blanc vaut 0 (une infinité de blancs = des zéros non écrits), la barre 1, les autres 2, 3, ..."""
    autres = sorted(machine.symboles() - {BLANC, BARRE})
    codes = {BLANC: 0, BARRE: 1}
    for k, s in enumerate(autres):
        codes[s] = k + 2
    return codes


def trois_compteurs(machine):
    """Traduit une machine de Turing en machine à compteurs g, d, t (plus Z, toujours nul).
    Renvoie (programme, codes des symboles, base b)."""
    codes = codes_symboles(machine)
    b = max(2, len(codes))
    symb = {c: s for s, c in codes.items()}
    a = Assembleur()
    etats = sorted(machine.etats())
    debut = {q: "lire_" + q for q in etats}
    a.dec_nulle(debut[machine.etat_initial])                  # instruction 0 : aller à l'état initial
    for q in etats:
        # lire : t := d // b, d := 0, et l'on sait le reste r = case lue
        sorties = [a.neuf("lu") for _ in range(b)]
        a.diviser(D, T, b, debut[q], sorties)
        for r in range(b):
            s = symb.get(r, BLANC)
            regle = machine.table.get((q, s))
            a.ici(sorties[r])
            e1, e2, e3, e4 = (a.neuf() for _ in range(4))
            if regle is None:
                # arrêt : on remet d = b*t + r, puis STOP
                a.dec_nulle(e1)
                a.transferer(T, D, b, e1, e2)
                arret = a.neuf("arret")
                a.ajouter(D, r, e2, arret)
                a.ici(arret)
                a.stop()
                continue
            action, q2 = regle[2], regle[3]
            a.dec_nulle(e1)
            if action == "R":
                # g := b*g + r (en passant par d, qui vaut 0), puis d := t
                a.transferer(G, D, b, e1, e2)
                a.ajouter(D, r, e2, e3)
                a.transferer(D, G, 1, e3, e4)
                a.transferer(T, D, 1, e4, debut[q2])
            elif action == "L":
                # d := b*t + r ; t := g // b ; g := t ; d := b*d + (reste de g)
                e5 = a.neuf()
                a.transferer(T, D, b, e1, e2)
                a.ajouter(D, r, e2, e3)
                rg = [a.neuf("g") for _ in range(b)]
                a.diviser(G, T, b, e3, rg)
                for r2 in range(b):
                    f1, f2, f3, f4 = (a.neuf() for _ in range(4))
                    a.ici(rg[r2])
                    a.dec_nulle(f1)
                    a.transferer(T, G, 1, f1, f2)
                    a.transferer(D, T, b, f2, f3)
                    a.ajouter(T, r2, f3, f4)
                    a.transferer(T, D, 1, f4, debut[q2])
            else:
                # écrire : d := b*t + code(action)
                a.transferer(T, D, b, e1, e2)
                a.ajouter(D, codes[action], e2, debut[q2])
    return a.assembler(), codes, b


def valeurs_initiales(codes, b, args):
    bande = bande_initiale(args)
    d = sum(codes[s] * b ** i for i, s in bande.items())
    return [0, d, 0, 0]


def bande_depuis_compteurs(g, d, b, codes):
    symb = {c: s for s, c in codes.items()}
    bande, i = {}, 0
    while d:
        d, r = divmod(d, b)
        if r:
            bande[i] = symb[r]
        i += 1
    i = -1
    while g:
        g, r = divmod(g, b)
        if r:
            bande[i] = symb[r]
        i -= 1
    return bande


# --------------------------------------------------------------------------- étape 2
PREMIERS = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
A, B = 0, 1


def deux_compteurs(programme, k):
    """Traduit un programme à k compteurs en programme à deux compteurs A, B :
    le contenu (c_0, ..., c_{k-1}) est rangé dans A = 2^c0 3^c1 5^c2 ..., B valant 0 entre deux fragments."""
    a = Assembleur()
    deb = ["i%d" % n for n in range(len(programme))]
    for n, ins in enumerate(programme):
        if ins[0] == "STOP":
            a.ici(deb[n])
            a.stop()
            continue
        if ins[0] == "DEC" and ins[2] == ins[3]:
            # simple saut : B vaut 0, donc DEC(B) échoue toujours
            a.ici(deb[n])
            a.dec(B, deb[ins[2]], deb[ins[2]])
            continue
        p = PREMIERS[ins[1]]
        if ins[0] == "INC":
            # A := p*A : on vide A dans B en multipliant par p, puis B dans A
            m = a.neuf()
            a.transferer(A, B, p, deb[n], m)
            a.transferer(B, A, 1, m, deb[ins[2]])
            continue
        # DEC : B := A // p ; le reste rho est connu par l'instruction où la division s'arrête
        restes = [a.neuf("rho") for _ in range(p)]
        a.diviser(A, B, p, deb[n], restes)
        # reste 0 : le compteur était > 0 ; A := A / p, puis succès
        a.transferer(B, A, 1, restes[0], deb[ins[2]])
        for r in range(1, p):
            # reste r > 0 : le compteur valait 0 ; on reconstitue A = p*B + r, puis échec
            e = a.neuf()
            a.ajouter(A, r, restes[r], e)
            a.transferer(B, A, p, e, deb[ins[3]])
    return a.assembler()


# --------------------------------------------------------------------------- vérification
def deux_compteurs_depuis_turing(machine):
    prog3, codes, b = trois_compteurs(machine)
    prog2 = deux_compteurs(prog3, 4)
    return prog3, prog2, codes, b


def comparer(machine, *args, deux=True):
    """Exécute la machine de Turing, la machine à trois compteurs et la machine à deux compteurs,
    et vérifie que la bande finale est la même. Renvoie un dictionnaire de mesures."""
    c = machine.executer(*args)
    attendu = {i - c.position: s for i, s in c.bande.items() if s != BLANC}
    prog3, codes, b = trois_compteurs(machine)
    v0 = valeurs_initiales(codes, b, args)
    m3 = MachineCompteurs(prog3, v0)
    v3, pas3, _ = m3.executer(v0)
    assert v3[T] == 0 and v3[Z] == 0
    assert bande_depuis_compteurs(v3[G], v3[D], b, codes) == attendu, "trois compteurs : bande différente"
    res = {"pas_turing": c.pas, "barres": c.nombre_de_barres(), "instr3": len(prog3), "pas3": pas3,
           "base": b, "depart3": v0}
    if deux:
        prog2 = deux_compteurs(prog3, 4)
        a0 = 2 ** v0[G] * 3 ** v0[D] * 5 ** v0[T] * 7 ** v0[Z]
        v2, pas2, it2 = MachineCompteurs(prog2, [a0, 0]).executer([a0, 0])
        assert v2[1] == 0
        A_final, e = v2[0], [0, 0, 0, 0]
        for k, p in enumerate(PREMIERS[:4]):
            while A_final % p == 0:
                A_final //= p
                e[k] += 1
        assert A_final == 1 and e == v3, "deux compteurs : contenu différent"
        res.update({"instr2": len(prog2), "pas2": pas2, "iterations2": it2, "depart2": a0})
    return res


def _principal(argv):
    import os
    if len(argv) >= 2:
        machine = Machine.depuis_fichier(argv[1])
        args = [int(x) for x in argv[2:]]
    else:
        machine = Machine.depuis_fichier(os.path.join(os.path.dirname(os.path.abspath(__file__)), "exemples", "addition.tm"))
        args = [2, 1]
    r = comparer(machine, *args)
    print("Machine de Turing : %d quadruplets, %d pas, résultat %d." % (len(machine), r["pas_turing"], r["barres"]))
    print("Trois compteurs (base %d) : %d instructions ; départ (g, d, t) = (%d, %d, %d) ; %d pas."
          % (r["base"], r["instr3"], r["depart3"][0], r["depart3"][1], r["depart3"][2], r["pas3"]))
    p2 = str(r["pas2"])
    print("Deux compteurs : %d instructions ; départ A = 2^%d 3^%d (%d chiffres) ; %s pas (%d chiffres)."
          % (r["instr2"], r["depart3"][0], r["depart3"][1], len(str(r["depart2"])), p2 if len(p2) < 30 else p2[:12] + "…", len(p2)))
    print("Les trois exécutions donnent la même bande finale.")


if __name__ == "__main__":
    _principal(sys.argv)
