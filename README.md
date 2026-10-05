# ML-Based Classical Cipher Identifier and Auto-Decryptor

Mini project for **Information and Network Security (Course Code 202046708)**,
B.Tech Computer Engineering, Semester VII, CVM University.

Given a ciphertext, the tool does two things:

1. **Identifies** which classical cipher produced it (Caesar, Monoalphabetic, Vigenere,
   Rail Fence or Playfair) using a machine-learning classifier.
2. **Cracks** it automatically by recovering the key and the plaintext (for every cipher
   except Playfair).

A Streamlit web app ties both steps together.

## Project structure

| File | Purpose |
|---|---|
| `ciphers.py` | Encrypt and decrypt functions for all five ciphers, plus a random-key generator |
| `features.py` | Turns a ciphertext into numeric features (letter frequencies, Index of Coincidence, entropy, ...) |
| `train.py` | Generates the dataset, trains a Random Forest, saves the model and plots |
| `cryptanalysis.py` | Automatic key recovery for each cipher |
| `evaluate_crack.py` | Measures cracking success rate by cipher and text length |
| `app.py` | Streamlit demo app |
| `corpus.txt` | English text used to build the dataset and the quadgram scoring model |
| `confusion_matrix.png`, `feature_importance.png`, `crack_results.txt` | Results from a sample run |

## Quick start

You need Python 3.9 or newer.

### Option A: uv (recommended)
```bash
uv venv
# Windows (cmd):         .venv\Scripts\activate
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Mac / Linux:           source .venv/bin/activate
uv pip install -r requirements.txt
```

### Option B: pip
```bash
python -m venv venv
# activate as above, using the venv folder
pip install -r requirements.txt
```

### Run
```bash
python train.py                  # trains the model, creates cipher_model.joblib (about 1 min)
python -m streamlit run app.py   # opens the app at http://localhost:8501
python evaluate_crack.py         # optional: reproduce the cracking success table
python ciphers.py                # optional: round-trip test of all five ciphers
```

`train.py` uses `corpus.txt` if present and downloads an English text corpus
(Tiny Shakespeare) if it is missing. `quadgrams.pkl` is built automatically the first time
the app cracks a cipher. Both generated files (`cipher_model.joblib`, `quadgrams.pkl`) are
safe to delete; they are recreated by the steps above.

## How it works

### Step 1: Identification (machine learning)

**Dataset.** Random snippets of 100 to 400 letters are taken from the corpus and encrypted
with a fresh random key for each cipher (1,500 samples per cipher for training). Training
and test snippets come from different parts of the corpus, so the test set never overlaps
the training set.

**Features** (60 values per ciphertext):
- Raw and sorted letter frequencies
- Index of Coincidence (IC) and entropy
- Periodic IC (splits the text by possible key lengths to catch Vigenere)
- Chi-square distance from English letter frequencies
- Playfair clues: no letter J, no doubled digraphs
- Repeated trigram rate and text length

**Model.** Random Forest with 300 trees. Test accuracy on the sample run was about 99%
(see `confusion_matrix.png`).

| Cipher | What gives it away |
|---|---|
| Caesar | Sorted frequencies look like English, raw frequencies fit a single shift |
| Monoalphabetic | Sorted frequencies look like English, raw frequencies are scrambled |
| Rail Fence | Letters only move, so raw frequencies still match English (E, T, A on top) |
| Vigenere | Frequencies are flattened (IC about 0.04) but IC rises when split by the key length |
| Playfair | Flat frequencies, no J, never produces a doubled digraph |

### Step 2: Auto-decrypt (cryptanalysis)

| Cipher | Attack |
|---|---|
| Caesar | Try all 25 shifts and pick the one closest to English (chi-square) |
| Vigenere | Index of Coincidence for the key length, chi-square per column, then refine with quadgram scores |
| Rail Fence | Brute force 2 to 12 rails and keep the most English-like result |
| Monoalphabetic | Hill climbing on the 26-letter key, scored by English quadgram statistics |
| Playfair | Not supported (see limitations) |

"English-like" is measured with a quadgram model: the log-probability of every
four-letter sequence, built from `corpus.txt`.

**Measured success rate.** Success means the recovered plaintext matches the original on at
least 95% of letters. Each cell is 10 random trials. The quadgram model was built from
a part of the corpus separate from the test text.

| Cipher | 100 letters | 200 letters | 400 letters |
|---|---|---|---|
| Caesar | 10/10 | 10/10 | 10/10 |
| Vigenere | 9/10 | 10/10 | 10/10 |
| Rail Fence | 10/10 | 10/10 | 10/10 |
| Monoalphabetic | 4/10 | 6/10 | 10/10 |

Numbers can vary slightly between runs because texts and keys are random.

## Using the app

- **Generate a test sample** tab: pick a cipher, encrypt sample text with a random key, and
  see the model's prediction and the auto-decrypted result. Best for demos.
- **Identify a ciphertext** tab: paste your own ciphertext (50 letters minimum, 100 or more
  recommended).

## Limitations

- **Short texts.** Identification works best with 100 or more letters, and accuracy drops
  below that.
- **Monoalphabetic cracking** needs roughly 300 or more letters to be reliable. With 26!
  possible keys and little text, several keys look equally plausible.
- **Playfair is identified but not cracked.** The usual attack (simulated annealing on the
  5x5 square) was too slow in pure Python and did not succeed on the test lengths.
- **Classical ciphers only.** Modern ciphers such as AES and DES produce near-random output
  that these statistics cannot tell apart.
- **Caesar vs Monoalphabetic** is the most common misclassification, because a Caesar shift
  is a special case of monoalphabetic substitution.
- **Corpus.** The scoring model comes from Shakespeare, so modern vocabulary can cause a few
  wrong letters in recovered text. A larger modern corpus would improve this.
- **Output format.** Only letters are kept, so recovered plaintext has no spaces.
- **Data.** All training data is synthetic and generated from one corpus, so accuracy on
  real-world ciphertext may be lower than the reported figures.

## Syllabus mapping

| Syllabus item | Where it appears |
|---|---|
| Unit 1: Symmetric cipher model, substitution and transposition techniques | `ciphers.py` (Practicals 1 to 6) |
| Unit 1: Security attacks | `cryptanalysis.py` (frequency analysis, brute force, hill climbing) |
| Course Outcome CO-1 | Understanding attacks on classical encryption through automated cryptanalysis |

## Future work

- Add Playfair cracking (faster annealing or a NumPy implementation)
- Add Hill and Columnar Transposition ciphers (also in the practical list)
- Compare Random Forest with other models (Logistic Regression, KNN, a small neural network)
- Train on more varied text, including modern English
- Detect cipher modes of modern algorithms (for example ECB patterns)