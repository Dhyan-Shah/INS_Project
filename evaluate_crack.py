"""Measure how often each cracker recovers the plaintext.

The quadgram model is built from the first 70% of the corpus and the test snippets
come from the last 30%, so the cracker never sees the text it is tested on.

Run:  python evaluate_crack.py
"""
import random
import sys
import time

from ciphers import CIPHER_NAMES, clean, encrypt_random
from cryptanalysis import CRACKERS, build_scorer, crack

TRIALS = 10
LENGTHS = [100, 200, 400]
SEED = 7


def letter_match(a: str, b: str) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    return sum(x == y for x, y in zip(a[:n], b[:n])) / n


def main():
    random.seed(SEED)
    with open("corpus.txt", encoding="utf-8", errors="ignore") as f:
        corpus = clean(f.read())
    cut = int(len(corpus) * 0.7)
    scorer = build_scorer(corpus[:cut])
    test_text = corpus[cut:]

    ciphers = [c for c in CIPHER_NAMES if c in CRACKERS] if len(sys.argv) < 2 else sys.argv[1:]
    print(f"Success = recovered plaintext matches original on >= 95% of letters "
          f"({TRIALS} trials each)\n")
    print(f"{'Cipher':<16}" + "".join(f"{L:>10} letters" for L in LENGTHS) + "   avg time")
    for cipher in ciphers:
        row, t_total, runs = [], 0.0, 0
        for L in LENGTHS:
            ok = 0
            for _ in range(TRIALS):
                start = random.randint(0, len(test_text) - L - 1)
                plain = test_text[start:start + L]
                ct = encrypt_random(plain, cipher)
                t0 = time.time()
                res = crack(cipher, ct, scorer)
                t_total += time.time() - t0
                runs += 1
                if letter_match(res["plaintext"], plain) >= 0.95:
                    ok += 1
            row.append(f"{ok}/{TRIALS}")
        print(f"{cipher:<16}" + "".join(f"{r:>17}" for r in row) + f"   {t_total / runs:.1f}s")


if __name__ == "__main__":
    main()
