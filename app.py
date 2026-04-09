import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.preprocessing import load_and_clean_data
try:
    from data.model import get_embeddings, recommend_books
except ModuleNotFoundError:
    st.error("Error: model.py not found. Please ensure model.py is in the same directory.")

st.title(" Book Recommendation System")

# Use autodetect in preprocessing; pass no path to auto-find the CSV
df = load_and_clean_data()

embeddings = get_embeddings(df['content'].tolist())

book = st.selectbox("Select a book:", df['title'])

if st.button("Recommend"):
    idx = df[df['title'] == book].index[0]

    recs = recommend_books(
        embeddings[idx],
        embeddings,
        df
    )

    for title, score in recs:
        st.write(f" {title} ({score:.2f})")