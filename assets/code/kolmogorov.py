"""Complexité de Kolmogorov : quelques expériences.

1. Le codage auto-délimitant  w -> 1^|w| 0 w  et son décodage.
2. Des bornes SUPÉRIEURES de la complexité par compression (zlib) :
   une borne inférieure, elle, ne se calcule pas (chapitre 14).
"""
import os, zlib

def auto(w):                      # codage auto-délimitant
    return "1" * len(w) + "0" + w

def lire_auto(s):                 # renvoie (w, reste)
    k = s.index("0")
    return s[k + 1:2 * k + 1], s[2 * k + 1:]

def mot(n):                       # bijection N -> {0,1}* : 0->'', 1->'0', 2->'1', 3->'00'...
    return bin(n + 1)[3:]

def entier(w):
    return int("1" + w, 2) - 1

if __name__ == "__main__":
    e, p = mot(12), "0110"
    code = auto(e) + p
    print("e =", 12, "->", e, "; programme", p, "; entrée de U :", code)
    print("décodage :", lire_auto(code), "-> e =", entier(lire_auto(code)[0]))
    assert all(entier(mot(n)) == n for n in range(1000))

    n = 100_000
    exemples = {
        "zéros": bytes(n),
        "motif 'ab' répété": b"ab" * (n // 2),
        "décimales de 1/7": ("142857" * (n // 6 + 1))[:n].encode(),
        "octets aléatoires": os.urandom(n),
    }
    for nom, x in exemples.items():
        print(f"{nom:22s} {8*len(x):7d} bits -> au plus {8*len(zlib.compress(x, 9)):7d} bits")
