"""Classical ciphers used to generate the labelled dataset.

All functions take plain text, keep only letters A-Z (uppercase) and return
ciphertext as an uppercase string.
"""
import random
import string

ALPHABET = string.ascii_uppercase


def clean(text: str) -> str:
    """Keep only letters and uppercase them."""
    return "".join(c for c in text.upper() if c in ALPHABET)


# ---------------------------------------------------------------- Caesar
def caesar_encrypt(text: str, shift: int) -> str:
    return "".join(ALPHABET[(ALPHABET.index(c) + shift) % 26] for c in clean(text))


def caesar_decrypt(text: str, shift: int) -> str:
    return caesar_encrypt(text, -shift)


# ------------------------------------------------------- Monoalphabetic
def random_mono_key() -> str:
    letters = list(ALPHABET)
    random.shuffle(letters)
    return "".join(letters)


def mono_encrypt(text: str, key: str) -> str:
    table = {p: k for p, k in zip(ALPHABET, key)}
    return "".join(table[c] for c in clean(text))


def mono_decrypt(text: str, key: str) -> str:
    table = {k: p for p, k in zip(ALPHABET, key)}
    return "".join(table[c] for c in clean(text))


# ------------------------------------------- Polyalphabetic (Vigenere)
def vigenere_encrypt(text: str, key: str) -> str:
    key = clean(key)
    out = []
    for i, c in enumerate(clean(text)):
        shift = ALPHABET.index(key[i % len(key)])
        out.append(ALPHABET[(ALPHABET.index(c) + shift) % 26])
    return "".join(out)


def vigenere_decrypt(text: str, key: str) -> str:
    key = clean(key)
    out = []
    for i, c in enumerate(clean(text)):
        shift = ALPHABET.index(key[i % len(key)])
        out.append(ALPHABET[(ALPHABET.index(c) - shift) % 26])
    return "".join(out)


# ------------------------------------------------------------- Rail Fence
def _rail_pattern(n: int, rails: int):
    pattern, rail, step = [], 0, 1
    for _ in range(n):
        pattern.append(rail)
        if rails > 1:
            if rail == 0:
                step = 1
            elif rail == rails - 1:
                step = -1
            rail += step
    return pattern


def railfence_encrypt(text: str, rails: int) -> str:
    text = clean(text)
    pattern = _rail_pattern(len(text), rails)
    fence = [[] for _ in range(rails)]
    for ch, r in zip(text, pattern):
        fence[r].append(ch)
    return "".join("".join(row) for row in fence)


def railfence_decrypt(text: str, rails: int) -> str:
    text = clean(text)
    pattern = _rail_pattern(len(text), rails)
    order = sorted(range(len(text)), key=lambda i: pattern[i])
    out = [""] * len(text)
    for ch, pos in zip(text, order):
        out[pos] = ch
    return "".join(out)


# --------------------------------------------------------------- Playfair
def _playfair_square(key: str):
    key = clean(key).replace("J", "I")
    seen = []
    for c in key + ALPHABET.replace("J", ""):
        if c not in seen:
            seen.append(c)
    return [seen[i:i + 5] for i in range(0, 25, 5)]


def _find(square, ch):
    for r in range(5):
        for c in range(5):
            if square[r][c] == ch:
                return r, c


def _playfair_pairs(text: str):
    text = clean(text).replace("J", "I")
    pairs, i = [], 0
    while i < len(text):
        a = text[i]
        b = text[i + 1] if i + 1 < len(text) else "X"
        if a == b:
            b = "X" if a != "X" else "Q"
            i += 1
        else:
            i += 2
        pairs.append((a, b))
    return pairs


def playfair_encrypt(text: str, key: str) -> str:
    sq = _playfair_square(key)
    out = []
    for a, b in _playfair_pairs(text):
        ra, ca = _find(sq, a)
        rb, cb = _find(sq, b)
        if ra == rb:
            out += [sq[ra][(ca + 1) % 5], sq[rb][(cb + 1) % 5]]
        elif ca == cb:
            out += [sq[(ra + 1) % 5][ca], sq[(rb + 1) % 5][cb]]
        else:
            out += [sq[ra][cb], sq[rb][ca]]
    return "".join(out)


def playfair_decrypt(text: str, key: str) -> str:
    sq = _playfair_square(key)
    text = clean(text)
    out = []
    for i in range(0, len(text) - 1, 2):
        ra, ca = _find(sq, text[i])
        rb, cb = _find(sq, text[i + 1])
        if ra == rb:
            out += [sq[ra][(ca - 1) % 5], sq[rb][(cb - 1) % 5]]
        elif ca == cb:
            out += [sq[(ra - 1) % 5][ca], sq[(rb - 1) % 5][cb]]
        else:
            out += [sq[ra][cb], sq[rb][ca]]
    return "".join(out)


# ------------------------------------------------ Random-key dispatcher
CIPHER_NAMES = ["Caesar", "Monoalphabetic", "Vigenere", "Rail Fence", "Playfair"]


def random_key_word(min_len=3, max_len=10) -> str:
    return "".join(random.choice(ALPHABET) for _ in range(random.randint(min_len, max_len)))


def encrypt_random(text: str, cipher: str) -> str:
    """Encrypt `text` with `cipher` using a freshly generated random key."""
    if cipher == "Caesar":
        return caesar_encrypt(text, random.randint(1, 25))
    if cipher == "Monoalphabetic":
        return mono_encrypt(text, random_mono_key())
    if cipher == "Vigenere":
        return vigenere_encrypt(text, random_key_word())
    if cipher == "Rail Fence":
        return railfence_encrypt(text, random.randint(2, 6))
    if cipher == "Playfair":
        return playfair_encrypt(text, random_key_word(4, 10))
    raise ValueError(f"Unknown cipher: {cipher}")


if __name__ == "__main__":
    msg = "Meet me at the old library after the lecture tomorrow"
    assert caesar_decrypt(caesar_encrypt(msg, 7), 7) == clean(msg)
    k = random_mono_key()
    assert mono_decrypt(mono_encrypt(msg, k), k) == clean(msg)
    assert vigenere_decrypt(vigenere_encrypt(msg, "LEMON"), "LEMON") == clean(msg)
    assert railfence_decrypt(railfence_encrypt(msg, 4), 4) == clean(msg)
    print("Playfair:", playfair_decrypt(playfair_encrypt(msg, "MONARCHY"), "MONARCHY"))
    print("All round-trip checks passed.")
