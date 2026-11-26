#!/usr/bin/env python3
"""Le problème de l'arrêt : l'argument diagonal, exécuté (chapitre « Indécidabilité » du manuel).

On se donne un « décideur » candidat : une fonction Python decide(source, x) qui prétend
répondre True si le programme de texte `source` s'arrête sur l'entrée x, False sinon.
paradoxe(decide) fabrique le programme D qui
    - obtient son propre texte (théorème de récursion : voir recursion.py),
    - demande au décideur « D s'arrête-t-il sur son propre texte ? »,
    - fait le contraire : boucle sans fin si la réponse est oui, s'arrête si elle est non.
Quel que soit le candidat, il se trompe sur D. Le programme le constate pour plusieurs
candidats, dont un qui simule le programme pendant un nombre de pas fixé.

Une exécution « sans fin » ne peut pas être observée jusqu'au bout : on l'exécute avec un
budget de pas et l'on constate qu'elle ne s'est pas arrêtée. Pour D, le texte du programme
montre directement qu'il boucle (« while True: pass »).

    python3 arret.py

Licence MIT. Frédéric Prost et Claude.
"""
import sys
import textwrap

from recursion import point_fixe


class BudgetEpuise(Exception):
    pass


def lancer(source, x, budget=200000):
    """Exécute la fonction programme(x) définie par `source`, avec au plus `budget` lignes exécutées.
    Renvoie ("arrêt", valeur) ou ("pas d'arrêt dans le budget", None)."""
    env = {}
    exec(source, env)
    compteur = [0]

    def trace(frame, event, arg):
        if event == "line":
            compteur[0] += 1
            if compteur[0] > budget:
                raise BudgetEpuise()
        return trace

    ancien = sys.gettrace()
    sys.settrace(trace)
    try:
        v = env["programme"](x)
        return "arrêt", v
    except BudgetEpuise:
        return "pas d'arrêt dans le budget", None
    finally:
        sys.settrace(ancien)


def paradoxe(source_decideur):
    """Texte du programme diagonal D associé au décideur (donné par son texte, qui définit decide)."""
    corps = source_decideur + textwrap.dedent("""
        def programme(x):
            if decide(MOI, MOI):
                while True:
                    pass
            return 0
        """)
    return point_fixe(corps)


CANDIDATS = {
    "répond toujours oui": "def decide(source, x):\n    return True\n",
    "répond toujours non": "def decide(source, x):\n    return False\n",
    "cherche le mot « while » dans le texte": "def decide(source, x):\n    return 'while' not in source\n",
    "simule 1000 lignes et conclut": textwrap.dedent("""\
        def decide(source, x):
            # Exécute le programme pendant au plus 1000 lignes (simulations imbriquées comprises) :
            # s'il s'est arrêté, répondre oui ; sinon, répondre non.
            import sys
            externe = not hasattr(sys, "_budget_decide")
            if externe:
                sys._budget_decide = [0]
            n = sys._budget_decide
            env = {}
            exec(source, env)
            class Stop(Exception):
                pass
            def t(f, e, a):
                if e == "line":
                    n[0] += 1
                    if n[0] > 1000:
                        raise Stop()
                return t
            old = sys.gettrace()
            sys.settrace(t)
            try:
                env["programme"](x)
                return True
            except Stop:
                return False
            finally:
                sys.settrace(old)
                if externe:
                    del sys._budget_decide
        """),
}


def _principal():
    for nom, dec in CANDIDATS.items():
        D = paradoxe(dec)
        env = {}
        exec(D, env)
        reponse = env["decide"](D, D)
        etat, _ = lancer(D, D)
        print("Candidat « %s »" % nom)
        print("   il affirme que D %s sur son propre texte" % ("s'arrête" if reponse else "ne s'arrête pas"))
        print("   en réalité, D : %s" % etat)
        juste = (reponse and etat == "arrêt") or (not reponse and etat != "arrêt")
        print("   le candidat se trompe : %s\n" % ("non" if juste else "oui"))
        assert not juste
    print("Aucun candidat n'échappe à son programme diagonal : c'est le théorème de Turing (1936).")


if __name__ == "__main__":
    _principal()
