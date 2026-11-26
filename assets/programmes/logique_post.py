"""logique_post.py : du problème de Post à la logique du premier ordre (réduction de Floyd).

À une liste de dominos (u_1/v_1, ..., u_k/v_k) on associe l'énoncé

    phi = [ ET_i P(u_i, v_i)  et  pour tous x, y : P(x, y) -> ET_i P(x.u_i, y.v_i) ]  ->  il existe z : P(z, z)

où P est un symbole de relation binaire, e une constante (le mot vide), et « x.w » le terme obtenu en
ajoutant à x les lettres de w une par une. Deux façons d'écrire ce terme :
  * avec une fonction unaire f_a par lettre a : x.ab = f_b(f_a(x)) ;
  * avec UNE seule fonction binaire c (concaténer une lettre) et une constante par lettre : x.ab = c(c(x, a), b).
La seconde n'utilise que des symboles d'arité au plus deux : une relation binaire, une fonction binaire,
des constantes. phi est valide (vraie dans toute structure) si et seulement si les dominos ont une solution.

Avec post.py, on obtient, pour toute machine de Turing Z et toute entrée x, un énoncé valide si et
seulement si Z s'arrête sur x : la validité n'est donc pas décidable (théorème de Church et Turing).

    python3 logique_post.py                   # l'exemple a/baa, ab/aa, bba/bb : énoncé et déduction
    python3 logique_post.py --tptp            # l'énoncé au format TPTP, pour un démonstrateur (E, Vampire)
    python3 logique_post.py --machine exemples/successeur.tm 0

Licence MIT. Auteurs : Frédéric Prost et Claude.
"""
import sys

import post


def terme(x, mot, binaire, noms):
    """Le terme x.mot, écrit avec des fonctions unaires f_a ou avec la fonction binaire c."""
    t = x
    for a in mot:
        t = "c(%s,%s)" % (t, noms[a]) if binaire else "f_%s(%s)" % (noms[a], t)
    return t


def noms_lettres(dominos):
    lettres = sorted({a for h, b in dominos for a in h + b})
    return {a: "l%d" % k for k, a in enumerate(lettres)}


def enonce(dominos, binaire=True, tptp=False):
    """L'énoncé de Floyd, en notation lisible ou au format TPTP (fof)."""
    noms = noms_lettres(dominos)
    if tptp:
        X, Y, Z, E = "X", "Y", "Z", "e"
        base = " & ".join("p(%s,%s)" % (terme(E, h, binaire, noms), terme(E, b, binaire, noms)) for h, b in dominos)
        pas = " & ".join("p(%s,%s)" % (terme(X, h, binaire, noms), terme(Y, b, binaire, noms)) for h, b in dominos)
        return "fof(post, conjecture, ( ( (%s) & ! [X,Y] : ( p(X,Y) => (%s) ) ) => ? [Z] : p(Z,Z) ) )." % (base, pas)
    base = " ∧ ".join("P(%s, %s)" % (terme("e", h, binaire, noms), terme("e", b, binaire, noms)) for h, b in dominos)
    pas = " ∧ ".join("P(%s, %s)" % (terme("x", h, binaire, noms), terme("y", b, binaire, noms)) for h, b in dominos)
    return "[ %s ∧ ∀x ∀y ( P(x, y) → %s ) ] → ∃z P(z, z)" % (base, pas)


def deduction(dominos, solution, binaire=True):
    """Si la suite d'indices est une solution, la liste des faits P(s, t) que l'on déduit des hypothèses,
    un domino après l'autre ; le dernier est de la forme P(t, t), ce qui prouve la conclusion."""
    noms = noms_lettres(dominos)
    h, b = dominos[solution[0]]
    faits = [(terme("e", h, binaire, noms), terme("e", b, binaire, noms))]
    for i in solution[1:]:
        u, v = dominos[i]
        x, y = faits[-1]
        faits.append((terme(x, u, binaire, noms), terme(y, v, binaire, noms)))
    return faits


def modele_des_mots(dominos, profondeur):
    """Le modèle « naturel » : les objets sont les mots, e est le mot vide, x.w est la concaténation,
    et P(x, y) est vrai si (x, y) s'obtient en enchaînant des dominos. Les hypothèses de phi y sont vraies,
    et la conclusion y est vraie si et seulement si les dominos ont une solution. On énumère les couples
    obtenus avec au plus « profondeur » dominos et l'on cherche un couple (z, z)."""
    couples = {d: [i] for i, d in enumerate(dominos)}
    front = dict(couples)
    for _ in range(profondeur):
        for (x, y), s in front.items():
            if x == y:
                return s
        nouveau = {}
        for (x, y), s in front.items():
            for i, (u, v) in enumerate(dominos):
                c = (x + u, y + v)
                n = min(len(c[0]), len(c[1]))
                if c[0][:n] == c[1][:n] and c not in couples:
                    couples[c] = s + [i]
                    nouveau[c] = s + [i]
        front = nouveau
    for (x, y), s in front.items():
        if x == y:
            return s
    return None


def _principal(argv):
    if "--machine" in argv:
        from machines import Machine
        k = argv.index("--machine")
        machine = Machine.depuis_fichier(argv[k + 1])
        args = [int(a) for a in argv[k + 2:] if not a.startswith("--")]
        dm, noms = post.dominos_modifies(machine, *args)
        dominos = post.vers_ordinaire(dm)
        sol = post.solution_ordinaire(post.solution_depuis_calcul(machine, dm, noms, *args), len(dm))
        e = enonce(dominos, tptp="--tptp" in argv)
        print("Machine de %d quadruplets -> %d dominos -> énoncé de %d caractères." % (len(machine), len(dominos), len(e)))
        if "--tptp" in argv:
            print(e)
        f = deduction(dominos, sol)
        assert f[-1][0] == f[-1][1]
        print("La machine s'arrête : la déduction compte %d étapes et aboutit à P(t, t), avec t de %d caractères."
              % (len(f), len(f[-1][0])))
        return
    dominos = [(("a",), ("b", "a", "a")), (("a", "b"), ("a", "a")), (("b", "b", "a"), ("b", "b"))]
    if "--tptp" in argv:
        print(enonce(dominos, tptp=True))
        return
    print("Dominos : a/baa, ab/aa, bba/bb (lettres a = l0, b = l1)")
    print("Énoncé, avec une fonction binaire c :")
    print("  " + enonce(dominos))
    print("Le même, avec des fonctions unaires :")
    print("  " + enonce(dominos, binaire=False))
    sol = modele_des_mots(dominos, 8)
    print("Solution trouvée dans le modèle des mots :", [i + 1 for i in sol])
    for x, y in deduction(dominos, sol):
        print("  P(%s, %s)" % (x, y))
    print("Le dernier fait est P(t, t) : l'énoncé est démontré.")


if __name__ == "__main__":
    _principal(sys.argv)
