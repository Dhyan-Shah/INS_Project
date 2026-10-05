"""Automatic cryptanalysis: recover the key and plaintext for each cipher.

Methods used
- Caesar ............ try all 25 shifts, pick the one closest to English (chi-square)
- Vigenere .......... Index of Coincidence to find the key length, then chi-square
                      on each column (each column is just a Caesar cipher)
- Rail Fence ........ brute force 2..12 rails, pick the most English-like result
- Monoalphabetic .... hill climbing on the key, scored by English quadgram statistics
- Playfair .......... NOT supported (identified by the classifier only; key search
                      is too slow and unreliable for short texts)

"Most English-like" is measured with a quadgram model (log-probabilities of
4-letter sequences) built from corpus.txt.
"""
import math
import os
import pickle
import random
from collections import Counter

import numpy as np

from ciphers import (ALPHABET, caesar_decrypt, clean, mono_decrypt,
                     railfence_decrypt, vigenere_decrypt)
from features import ENGLISH_FREQ, index_of_coincidence

CORPUS_FILE = "corpus.txt"
QUADGRAM_FILE = "quadgrams.pkl"


# ------------------------------------------------------- Quadgram scorer
class QuadgramScorer:
    """Scores text by how English-like its 4-letter sequences are."""

    def __init__(self, counts: Counter):
        total = sum(counts.values())
        self.logp = {q: math.log10(c / total) for q, c in counts.items()}
        self.floor = math.log10(0.01 / total)

    def score(self, text: str) -> float:
        get, floor = self.logp.get, self.floor
        return sum(get(text[i:i + 4], floor) for i in range(len(text) - 3))


def build_scorer(corpus_text: str = None) -> QuadgramScorer:
    if corpus_text is None:
        with open(CORPUS_FILE, encoding="utf-8", errors="ignore") as f:
            corpus_text = clean(f.read())
    counts = Counter(corpus_text[i:i + 4] for i in range(len(corpus_text) - 3))
    return QuadgramScorer(counts)


def load_scorer() -> QuadgramScorer:
    if os.path.exists(QUADGRAM_FILE):
        with open(QUADGRAM_FILE, "rb") as f:
            return pickle.load(f)
    scorer = build_scorer()
    with open(QUADGRAM_FILE, "wb") as f:
        pickle.dump(scorer, f)
    return scorer


def chi_square(text: str) -> float:
    n = len(text)
    if n == 0:
        return float("inf")
    counts = Counter(text)
    expected = ENGLISH_FREQ * n
    return sum((counts.get(c, 0) - e) ** 2 / e for c, e in zip(ALPHABET, expected))


# ----------------------------------------------------------------- Caesar
def crack_caesar(ct: str, scorer=None):
    best = min(range(26), key=lambda s: chi_square(caesar_decrypt(ct, s)))
    return {"key": f"shift = {best}", "plaintext": caesar_decrypt(ct, best)}


# --------------------------------------------------------------- Vigenere
def _guess_key_length(ct: str, max_len: int = 16) -> int:
    scores = {}
    for L in range(1, max_len + 1):
        cols = [ct[i::L] for i in range(L)]
        scores[L] = float(np.mean([index_of_coincidence(c) for c in cols]))
    best = max(scores.values())
    # smallest length that is nearly as good as the best (avoids picking multiples)
    for L in range(1, max_len + 1):
        if scores[L] >= 0.88 * best and scores[L] > 0.05:
            return L
    return max(scores, key=scores.get)


def _refine_vigenere_key(ct: str, key: list, scorer, passes: int = 3):
    """Try every letter at each key position, keep whatever scores best."""
    best = scorer.score(vigenere_decrypt(ct, "".join(key)))
    for _ in range(passes):
        changed = False
        for i in range(len(key)):
            orig = key[i]
            for letter in ALPHABET:
                key[i] = letter
                s = scorer.score(vigenere_decrypt(ct, "".join(key)))
                if s > best:
                    best, orig, changed = s, letter, True
            key[i] = orig
        if not changed:
            break
    return key, best


def crack_vigenere(ct: str, scorer=None):
    # 1) candidate key lengths from the Index of Coincidence
    ic = {}
    for L in range(1, 17):
        cols = [ct[i::L] for i in range(L)]
        ic[L] = float(np.mean([index_of_coincidence(c) for c in cols]))
    top = max(ic.values())
    candidates = [L for L in range(1, 17) if ic[L] >= 0.85 * top and ic[L] > 0.05][:3]
    if not candidates:
        candidates = [max(ic, key=ic.get)]

    # 2) for each candidate: chi-square per column, then refine with quadgrams
    best_key, best_score = None, -1e18
    for L in candidates:
        key = []
        for i in range(L):
            col = ct[i::L]
            shift = min(range(26), key=lambda s: chi_square(caesar_decrypt(col, s)))
            key.append(ALPHABET[shift])
        key, score = _refine_vigenere_key(ct, key, scorer)
        if score > best_score:
            best_score, best_key = score, "".join(key)
    return {"key": f"{best_key} (length {len(best_key)})",
            "plaintext": vigenere_decrypt(ct, best_key)}


# -------------------------------------------------------------- Rail Fence
def crack_railfence(ct: str, scorer):
    best_r = max(range(2, 13), key=lambda r: scorer.score(railfence_decrypt(ct, r)))
    return {"key": f"rails = {best_r}", "plaintext": railfence_decrypt(ct, best_r)}


# ---------------------------------------------------------- Monoalphabetic
def crack_mono(ct: str, scorer, restarts: int = 12, iters: int = 4000, seed=None):
    rng = random.Random(seed)
    # start from frequency-matched guess, then random restarts
    by_freq_ct = [c for c, _ in Counter(ct).most_common()]
    by_freq_ct += [c for c in ALPHABET if c not in by_freq_ct]
    english_order = "ETAOINSHRDLCUMWFGYPBVKJXQZ"
    best_key, best_score = None, -1e18
    for r in range(restarts):
        if r == 0:
            key = dict(zip(english_order, by_freq_ct))   # plain letter -> cipher letter
            key = {p: key[p] for p in ALPHABET}
        else:
            letters = list(ALPHABET)
            rng.shuffle(letters)
            key = dict(zip(ALPHABET, letters))
        inv = {c: p for p, c in key.items()}
        cur = "".join(inv[c] for c in ct)
        cur_score = scorer.score(cur)
        for _ in range(iters):
            a, b = rng.sample(ALPHABET, 2)
            key[a], key[b] = key[b], key[a]
            inv = {c: p for p, c in key.items()}
            cand = "".join(inv[c] for c in ct)
            cand_score = scorer.score(cand)
            if cand_score > cur_score:
                cur_score = cand_score
            else:
                key[a], key[b] = key[b], key[a]
        if cur_score > best_score:
            best_score, best_key = cur_score, "".join(key[p] for p in ALPHABET)
    return {"key": best_key, "plaintext": mono_decrypt(ct, best_key)}


# --------------------------------------------------------------- Dispatcher
CRACKERS = {
    "Caesar": crack_caesar,
    "Vigenere": crack_vigenere,
    "Rail Fence": crack_railfence,
    "Monoalphabetic": crack_mono,
}


def crack(cipher: str, ciphertext: str, scorer=None) -> dict:
    if cipher not in CRACKERS:
        raise ValueError(f"Automatic cracking is not supported for {cipher}")
    ct = clean(ciphertext)
    if scorer is None:
        scorer = load_scorer()
    result = CRACKERS[cipher](ct, scorer)
    result["english_score"] = scorer.score(result["plaintext"]) / max(len(ct) - 3, 1)
    return result
