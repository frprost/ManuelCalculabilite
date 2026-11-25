"""Calculabilité et IA : trois petites expériences (chapitre « Calculabilité et intelligence artificielle »).

1. Synthèse par recherche aveugle pour une spécification testable.
2. La suite diagonale contre un prédicteur : il se trompe à chaque coup.
3. L'argument de Gold : un apprenant qui apprend tous les langages finis
   change d'avis indéfiniment sur un texte du langage infini {a^n : n >= 1}.
"""
from itertools import count


# 1. Spécification testable : psi(x, y) décidable, et pour tout x il existe y.
def synthese(psi):
    """Le programme  x -> mu y psi(x, y)  satisfait psi (lent, mais correct)."""
    return lambda x: next(y for y in count() if psi(x, y))


racine = synthese(lambda x, y: y * y <= x < (y + 1) * (y + 1))   # partie entière de sqrt(x)


# 2. Prédicteurs : une fonction de la liste des bits déjà vus vers le bit prédit.
def majorite(vus):
    return 1 if 2 * sum(vus) > len(vus) else 0


def dernier_motif(vus):
    """Cherche le plus long suffixe déjà vu plus tôt et prédit ce qui l'avait suivi."""
    for k in range(len(vus) - 1, 0, -1):
        suffixe = vus[-k:]
        for i in range(len(vus) - k - 1, -1, -1):
            if vus[i:i + k] == suffixe:
                return vus[i + k]
    return 0


def diagonale(predicteur, n):
    s = []
    for _ in range(n):
        s.append(1 - predicteur(s))   # on prend toujours le contraire de la prédiction
    return s


# 3. Gold. Un apprenant reçoit les mots un par un et propose un langage.
def apprenant_prudent(vus):
    """Propose l'ensemble fini des mots vus : il apprend tout langage fini."""
    return frozenset(vus)


def texte_de_gold(apprenant, etapes):
    """Construit le début du texte de Gold pour L = {a, aa, aaa, ...}."""
    texte, changements, devinette = [], 0, None
    for k in range(1, etapes + 1):
        mot = "a" * k
        cible = frozenset("a" * j for j in range(1, k + 1))
        while True:                      # on répète le mot jusqu'à ce que l'apprenant devine {a,...,a^k}
            texte.append(mot)
            nouvelle = apprenant(texte)
            if nouvelle != devinette:
                changements += 1
                devinette = nouvelle
            if nouvelle == cible:
                break
    return texte, changements


if __name__ == "__main__":
    print("1. racine entière par recherche aveugle :", [racine(x) for x in (0, 1, 15, 16, 99)])
    for nom, p in (("majorité", majorite), ("dernier motif", dernier_motif)):
        s = diagonale(p, 40)
        erreurs = sum(p(s[:i]) != s[i] for i in range(len(s)))
        print(f"2. prédicteur {nom:14s} suite {''.join(map(str, s[:24]))}...  erreurs : {erreurs}/40")
    texte, ch = texte_de_gold(apprenant_prudent, 10)
    print("3. Gold : après", len(texte), "mots, l'apprenant a changé", ch, "fois d'avis ;",
          "sur le texte infini, il en changera indéfiniment")
