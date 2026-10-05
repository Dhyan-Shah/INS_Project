# ML-Based Classical Cipher Identifier

Mini project for **Information and Network Security (202046708)**.
A machine-learning model that looks at a ciphertext and predicts which classical
cipher produced it: Caesar, Monoalphabetic, Vigenere, Rail Fence or Playfair.

## Files
| File | Purpose |
|---|---|
| `ciphers.py` | Encrypt/decrypt for all 5 ciphers + random-key generator |
| `features.py` | Feature extraction (frequencies, Index of Coincidence, entropy, ...) |
| `train.py` | Builds the dataset, trains a Random Forest, saves model and plots |
| `cryptanalysis.py` | Auto-decrypt: recovers key + plaintext for Caesar, Vigenere, Rail Fence, Monoalphabetic |
| `evaluate_crack.py` | Measures cracking success rate by cipher and text length |
| `app.py` | Streamlit demo app (identify, then auto-decrypt) |

## Run
```bash
pip install -r requirements.txt
python ciphers.py      # optional: round-trip test of all ciphers
python train.py        # generates data, trains, saves cipher_model.joblib
python evaluate_crack.py   # optional: success rate of the auto-decrypt step
streamlit run app.py   # opens the demo in your browser
```
`train.py` downloads an English text corpus (Tiny Shakespeare) on first run. To use
your own text instead, put it in `corpus.txt` next to the scripts.

## How it works
1. **Dataset**: random snippets (100-400 letters) of English text are encrypted with a
   fresh random key for each cipher. Train and test snippets come from different parts of
   the corpus, so there is no leakage.
2. **Features** (34 + 26 frequency values):
   - Letter frequencies (raw and sorted)
   - Index of Coincidence (IC) and entropy
   - Periodic IC (splits text by possible key lengths, catches Vigenere)
   - Chi-square distance from English letter frequencies
   - Playfair clues: no letter J, no doubled digraphs
   - Repeated trigram rate, text length
3. **Model**: Random Forest (300 trees).
4. **Result**: about 99% test accuracy (see `confusion_matrix.png`).

## Step 2: Auto-decrypt (cryptanalysis)
After the model names the cipher, the matching attack recovers the key:

| Cipher | Attack | Idea |
|---|---|---|
| Caesar | Chi-square over 25 shifts | The right shift makes letter frequencies look like English |
| Vigenere | Index of Coincidence for key length, chi-square per column, quadgram refinement | Each key position is a separate Caesar cipher |
| Rail Fence | Brute force 2-12 rails, score each result | Only ~11 possible keys |
| Monoalphabetic | Hill climbing on the key with English quadgram scores | Keyspace is 26! so brute force is impossible |
| Playfair | Not supported | Needs a long ciphertext and a slow key search (see limitations) |

"English-like" is measured with a quadgram model (log-probability of every 4-letter
sequence), built from `corpus.txt`.

**Measured success rate** (recovered plaintext matches on at least 95% of letters,
10 random trials each, test text held out from the quadgram model):

| Cipher | 100 letters | 200 letters | 400 letters |
|---|---|---|---|
| Caesar | 10/10 | 10/10 | 10/10 |
| Vigenere | 9/10 | 10/10 | 10/10 |
| Rail Fence | 10/10 | 10/10 | 10/10 |
| Monoalphabetic | 4/10 | 6/10 | 10/10 |

Results vary a little between runs because texts and keys are random.

## Why each cipher is distinguishable
| Cipher | Letter frequencies | Key clue |
|---|---|---|
| Caesar | Shifted English profile | Sorted frequencies look like English |
| Monoalphabetic | Permuted English profile | Sorted frequencies look like English, but raw ones don't fit a single shift |
| Rail Fence | Same as English (letters only move) | Raw frequencies match English: E, T, A on top |
| Vigenere | Flattened (IC about 0.04) | IC rises when split by the right key length |
| Playfair | Flattened, no J | No doubled digraphs, no letter J |

## Limitations (good to mention in the viva)
- Monoalphabetic cracking needs roughly 300+ letters to be reliable. With 26! possible keys
  and little text, several keys look equally plausible.
- The quadgram model comes from Shakespeare, so modern vocabulary can cause a few
  wrong letters in the recovered text. A larger, modern corpus would fix this.
- Playfair is identified but not cracked: the usual attack (simulated annealing) was too
  slow in pure Python and failed on our test lengths. Not a bug, a known hard case.
- Recovered plaintext has no spaces, because only letters are kept.
- Identification works best with 100+ letters; accuracy drops on very short texts.
- Covers classical ciphers only. Modern ciphers (AES, DES) output near-random bytes,
  so they cannot be told apart by statistics like these.
- Caesar vs Monoalphabetic is the most common confusion, because a Caesar shift is just a
  special case of a monoalphabetic substitution.

## Syllabus mapping
- Unit 1: Symmetric cipher model, substitution and transposition techniques
- Practicals 1 to 6: the cipher implementations are reused here
- Course outcome CO-1: understanding attacks (this is automated cryptanalysis)

## Ideas for future work
Add Playfair cracking (faster annealing or a C/NumPy version), add Hill and Columnar Transposition, try a neural network, or extend to detect the cipher
mode of modern algorithms (for example ECB patterns).
