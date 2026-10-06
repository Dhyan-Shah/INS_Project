"""Streamlit demo: paste a ciphertext, get the predicted cipher.

Run:  streamlit run app.py   (after running train.py once)
"""
import os
import random

import joblib
import pandas as pd
import streamlit as st

from ciphers import CIPHER_NAMES, clean, encrypt_random
from cryptanalysis import CRACKERS, crack, load_scorer
from features import extract_features

st.set_page_config(page_title="Cipher Identifier", page_icon="🔐")
st.title("🔐 ML Cipher Identifier")
st.caption("Information and Network Security - Mini Project")


@st.cache_resource
def load_model():
    if not os.path.exists("cipher_model.joblib"):
        return None
    return joblib.load("cipher_model.joblib")


@st.cache_resource
def get_scorer():
    return load_scorer()


def show_crack(cipher: str, text: str, key_prefix: str):
    """Run the matching cracker and display key + plaintext."""
    if cipher not in CRACKERS:
        st.info(f"Automatic cracking is not supported for {cipher}. "
                "Playfair needs a long ciphertext and a slow key search.")
        return
    with st.spinner(f"Cracking {cipher}..."):
        result = crack(cipher, text, get_scorer())
    st.subheader("Auto-decrypt result")
    st.write(f"**Recovered key:** `{result['key']}`")
    st.text_area("Recovered plaintext (spaces are lost - only letters are kept)",
                 result["plaintext"], height=140, key=f"{key_prefix}_plaintext")
    if len(clean(text)) < 150:
        st.caption("Short ciphertext - the recovered text may contain errors.")


model = load_model()
if model is None:
    st.error("Model not found. Run `python train.py` first.")
    st.stop()

tab_predict, tab_demo = st.tabs(["Identify a ciphertext", "Generate a test sample"])

with tab_predict:
    text = st.text_area("Paste ciphertext (100+ letters works best)", height=160)
    if st.button("Identify cipher", type="primary"):
        letters = clean(text)
        if len(letters) < 50:
            st.warning("Please enter at least 50 letters.")
        else:
            probs = model.predict_proba([extract_features(letters)])[0]
            result = pd.Series(probs, index=model.classes_).sort_values(ascending=False)
            st.success(f"Predicted cipher: **{result.index[0]}** "
                       f"({result.iloc[0] * 100:.1f}% confidence)")
            st.bar_chart(result)
            if len(letters) < 100:
                st.info("Short text - accuracy drops below ~100 letters.")
            show_crack(result.index[0], letters, "identify")

with tab_demo:
    st.write("Encrypt sample English text with a random cipher, then test the model on it.")
    sample = st.text_area(
        "Plaintext",
        "Information security protects data from unauthorized access and "
        "ensures confidentiality integrity and availability across networks "
        "and computer systems used by organizations every single day",
        height=120)
    chosen = st.selectbox("Cipher", CIPHER_NAMES)
    if st.button("Encrypt with random key"):
        st.session_state["cipher_out"] = (chosen, encrypt_random(sample, chosen))
    if "cipher_out" in st.session_state:
        true_label, ct = st.session_state["cipher_out"]
        st.code(ct)
        probs = model.predict_proba([extract_features(ct)])[0]
        pred = model.classes_[probs.argmax()]
        st.write(f"True cipher: **{true_label}** | Model prediction: **{pred}**")
        if len(clean(ct)) < 100:
            st.info("Short samples are harder - try longer plaintext.")
        show_crack(pred, ct, "demo")