"""Turn a ciphertext into a numeric feature vector.

Why these features work:
- Caesar / Monoalphabetic only *substitute* letters, so the sorted letter
  frequency profile stays identical to English (high Index of Coincidence).
- Rail Fence only *rearranges* letters, so the raw frequencies stay English-like
  too (E, T, A still dominate) -- that is how it differs from substitution.
- Vigenere flattens frequencies (IC drops towards 0.038), but IC rises again
  when the text is split by the right key length.
- Playfair works on digraphs: no J, never produces a doubled pair, flat-ish IC.
"""
import math
from collections import Counter

import numpy as np

from ciphers import ALPHABET, clean

# Approximate English letter frequencies (A-Z)
ENGLISH_FREQ = np.array([
    8.17, 1.49, 2.78, 4.25, 12.70, 2.23, 2.02, 6.09, 6.97, 0.15, 0.77, 4.03, 2.41,
    6.75, 7.51, 1.93, 0.10, 5.99, 6.33, 9.06, 2.76, 0.98, 2.36, 0.15, 1.97, 0.07,
]) / 100.0


def index_of_coincidence(text: str) -> float:
    n = len(text)
    if n < 2:
        return 0.0
    counts = Counter(text)
    return sum(v * (v - 1) for v in counts.values()) / (n * (n - 1))


def entropy(text: str) -> float:
    n = len(text)
    counts = Counter(text)
    return -sum((v / n) * math.log2(v / n) for v in counts.values())


def periodic_ic(text: str, max_period: int = 12) -> float:
    """Best average IC after splitting the text into `p` columns (p = 2..max).

    High value => repeating key of that length => Vigenere-like.
    """
    best = 0.0
    for p in range(2, max_period + 1):
        cols = [text[i::p] for i in range(p)]
        avg = float(np.mean([index_of_coincidence(c) for c in cols]))
        best = max(best, avg)
    return best


def even_pair_doubles(text: str) -> float:
    """Fraction of (0,1),(2,3),... digraphs made of the same letter.

    Playfair never produces these, other ciphers do ~6% of the time.
    """
    pairs = [(text[i], text[i + 1]) for i in range(0, len(text) - 1, 2)]
    if not pairs:
        return 0.0
    return sum(a == b for a, b in pairs) / len(pairs)


def repeated_trigrams(text: str) -> float:
    tri = [text[i:i + 3] for i in range(len(text) - 2)]
    if not tri:
        return 0.0
    counts = Counter(tri)
    return sum(v - 1 for v in counts.values() if v > 1) / len(tri)


FEATURE_NAMES = (
    [f"freq_{c}" for c in ALPHABET]
    + [f"sorted_freq_{i}" for i in range(26)]
    + ["ic", "entropy", "periodic_ic", "chi_sq_english", "has_J",
       "even_pair_doubles", "repeated_trigrams", "length"]
)


def extract_features(ciphertext: str) -> np.ndarray:
    text = clean(ciphertext)
    n = max(len(text), 1)
    counts = Counter(text)
    freq = np.array([counts.get(c, 0) / n for c in ALPHABET])
    sorted_freq = np.sort(freq)[::-1]

    expected = ENGLISH_FREQ * n
    chi_sq = float(np.sum((freq * n - expected) ** 2 / expected))

    extras = [
        index_of_coincidence(text),
        entropy(text) if text else 0.0,
        periodic_ic(text),
        chi_sq,
        1.0 if "J" in text else 0.0,
        even_pair_doubles(text),
        repeated_trigrams(text),
        float(len(text)),
    ]
    return np.concatenate([freq, sorted_freq, extras])
