"""Automates cellulaires (chapitre « Autres modèles de calcul »).

1. Automates élémentaires : numérotation de Wolfram, règle 110, règle 90 et triangle de Pascal.
2. Simulation d'une machine de Turing par un automate cellulaire de rayon 1 : un pas de la
   machine = un pas de l'automate. Vérifiée sur le castor affairé à 3 états.
"""
from math import comb


def pas_elementaire(ligne, regle):
    """Une ligne finie, entourée de 0 (le motif peut s'étendre d'une case de chaque côté)."""
    l = [0, 0] + ligne + [0, 0]
    return [(regle >> (l[i - 1] << 2 | l[i] << 1 | l[i + 1])) & 1 for i in range(1, len(l) - 1)]


def evolution(regle, t, depart=(1,)):
    lignes = [list(depart)]
    for _ in range(t):
        lignes.append(pas_elementaire(lignes[-1], regle))
    return lignes


# Machine de Turing -> automate cellulaire ---------------------------------------
def regle_locale(delta):
    """Les états de l'automate sont des symboles s ou des couples (q, s) (tête en q sur s).
    La nouvelle valeur d'une case ne dépend que d'elle et de ses deux voisines."""
    def f(g, c, d):
        if isinstance(c, tuple):                    # la tête est ici : on écrit, elle s'en va
            q, s = c
            return delta[q, s][1] if (q, s) in delta else c      # état d'arrêt : on fige
        if isinstance(g, tuple) and g in delta and delta[g][2] == 'D':
            return (delta[g][0], c)                 # la tête arrive de la gauche
        if isinstance(d, tuple) and d in delta and delta[d][2] == 'G':
            return (delta[d][0], c)                 # la tête arrive de la droite
        return c
    return f


def pas_automate(f, config, blanc='0'):
    l = [blanc, blanc] + config + [blanc, blanc]   # la configuration peut grandir d'une case de chaque côté
    return [f(l[i - 1], l[i], l[i + 1]) for i in range(1, len(l) - 1)]


def machine_directe(delta, q0, n_pas, blanc='0'):
    bande, pos, q = {}, 0, q0
    for _ in range(n_pas):
        if (q, bande.get(pos, blanc)) not in delta:
            break
        q, s, d = delta[q, bande.get(pos, blanc)]
        bande[pos] = s
        pos += 1 if d == 'D' else -1
    return bande, pos, q


if __name__ == "__main__":
    print("1. règle 110 (départ : une cellule), 8 premières lignes :")
    for l in evolution(110, 7):
        print("   " + "".join("█" if x else "·" for x in l).rstrip("·").rjust(16))
    lignes = evolution(90, 31)
    ok90 = True
    for t, l in enumerate(lignes):
        # l a 2t+1 cases, d'indices j = -t..t
        for i, x in enumerate(l):
            j = i - t
            attendu = comb(t, (t + j) // 2) % 2 if (t + j) % 2 == 0 else 0
            ok90 &= (x == attendu)
    print("   règle 90 = triangle de Pascal modulo 2 sur 32 lignes :", ok90)
    print("   règle 240 décale d'une case :", evolution(240, 3, (1, 0, 1, 1))[3] == [0, 0, 0, 0, 0, 0, 1, 0, 1, 1])
    # 2. castor affairé à 3 états (A0 -> 1RB, ...), 14 pas, 6 uns
    delta = {('A', '0'): ('B', '1', 'D'), ('A', '1'): ('H', '1', 'D'),
             ('B', '0'): ('C', '0', 'D'), ('B', '1'): ('B', '1', 'D'),
             ('C', '0'): ('C', '1', 'G'), ('C', '1'): ('A', '1', 'G')}
    f = regle_locale(delta)
    config, gauche = [('A', '0')], 0                # gauche : position de la case 0 de la liste
    for t in range(20):
        config, gauche = pas_automate(f, config), gauche - 1
        bande, pos, q = machine_directe(delta, 'A', t + 1)
        tete = [i for i, c in enumerate(config) if isinstance(c, tuple)]
        assert len(tete) == 1 and tete[0] + gauche == pos and config[tete[0]][0] == q
        for i, c in enumerate(config):
            s = c[1] if isinstance(c, tuple) else c
            assert s == bande.get(i + gauche, '0')
    uns = sum((c[1] if isinstance(c, tuple) else c) == '1' for c in config)
    print("2. castor affairé à 3 états simulé par un automate cellulaire : identique à la machine",
          "pendant 20 pas ; état final", config[tete[0]][0], ";", uns, "symboles 1")
