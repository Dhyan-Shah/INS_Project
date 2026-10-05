"""Generate the dataset, train the model, evaluate and save everything.

Run:  python train.py
Needs an English corpus in corpus.txt (downloaded automatically if missing).
"""
import os
import random
import urllib.request

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score,
                             classification_report)

from ciphers import CIPHER_NAMES, clean, encrypt_random
from features import FEATURE_NAMES, extract_features

CORPUS_FILE = "corpus.txt"
CORPUS_URL = ("https://raw.githubusercontent.com/karpathy/char-rnn/"
              "master/data/tinyshakespeare/input.txt")
SAMPLES_PER_CIPHER = 1500      # per cipher, for training (test uses 30% of this)
MIN_LEN, MAX_LEN = 100, 400    # ciphertext length in letters
SEED = 42


def load_corpus() -> str:
    if not os.path.exists(CORPUS_FILE):
        print("Downloading English corpus...")
        urllib.request.urlretrieve(CORPUS_URL, CORPUS_FILE)
    with open(CORPUS_FILE, encoding="utf-8", errors="ignore") as f:
        return clean(f.read())


def make_dataset(corpus: str, n_per_cipher: int):
    X, y = [], []
    for cipher in CIPHER_NAMES:
        for _ in range(n_per_cipher):
            length = random.randint(MIN_LEN, MAX_LEN)
            start = random.randint(0, len(corpus) - length - 1)
            snippet = corpus[start:start + length]
            X.append(extract_features(encrypt_random(snippet, cipher)))
            y.append(cipher)
    return np.array(X), np.array(y)


def main():
    random.seed(SEED)
    np.random.seed(SEED)

    corpus = load_corpus()
    # Split the *source text* so test snippets never overlap training snippets
    cut = int(len(corpus) * 0.7)
    train_text, test_text = corpus[:cut], corpus[cut:]

    print("Generating training data...")
    X_train, y_train = make_dataset(train_text, SAMPLES_PER_CIPHER)
    print("Generating test data...")
    X_test, y_test = make_dataset(test_text, int(SAMPLES_PER_CIPHER * 0.3))

    print("Training Random Forest...")
    model = RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=-1)
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    print(f"\nTest accuracy: {accuracy_score(y_test, pred):.4f}\n")
    print(classification_report(y_test, pred))

    ConfusionMatrixDisplay.from_predictions(
        y_test, pred, labels=CIPHER_NAMES, xticks_rotation=30, cmap="Blues")
    plt.title("Cipher identification - confusion matrix")
    plt.tight_layout()
    plt.savefig("confusion_matrix.png", dpi=150)
    plt.close()

    # Top features
    order = np.argsort(model.feature_importances_)[::-1][:12]
    plt.figure(figsize=(7, 4))
    plt.barh([FEATURE_NAMES[i] for i in order][::-1],
             model.feature_importances_[order][::-1], color="#2a6fdb")
    plt.title("Top 12 feature importances")
    plt.tight_layout()
    plt.savefig("feature_importance.png", dpi=150)
    plt.close()

    joblib.dump(model, "cipher_model.joblib")
    print("Saved cipher_model.joblib, confusion_matrix.png, feature_importance.png")


if __name__ == "__main__":
    main()
