import streamlit as st
import sys
import os
import requests
import pandas as pd

# --------------------------
# IMPORT YOUR EXISTING MODULES
# --------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.preprocessing import load_and_clean_data

try:
    from data.model import get_embeddings, recommend_books
except ModuleNotFoundError:
    st.error("Error: model.py not found. Please ensure model.py is in the same directory.")

# --------------------------
# NETFLIX STYLE SETTINGS
# --------------------------
st.set_page_config(page_title="BookFlix", layout="wide", initial_sidebar_state="collapsed")

# Hide Streamlit's default elements
hide_st_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

[data-testid="stSidebar"] {
    display: none;
}

body {
    background-color: #141414;
    color: white;
    font-family: 'Netflix Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

.block-container {
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: none;
}

.book-card {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    margin-bottom: 10px;
}

.book-card:hover {
    transform: scale(1.05);
    box-shadow: 0 8px 25px rgba(0,0,0,0.5);
}

.book-title {
    font-size: 14px;
    font-weight: 500;
    text-align: center;
    margin-top: 8px;
    color: white;
    max-height: 40px;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}

.row-title {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 15px;
    color: white;
}

.search-container {
    background: linear-gradient(180deg, rgba(0,0,0,0.7) 0%, transparent 100%);
    padding: 60px 40px 40px;
    margin-bottom: 40px;
    border-radius: 10px;
}

.search-input {
    max-width: 600px;
    margin: 0 auto;
}

.stSelectbox > div > div {
    background-color: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 5px;
    color: white;
}

.stButton > button {
    background-color: #e50914;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 12px 24px;
    font-weight: bold;
    cursor: pointer;
    transition: background-color 0.3s ease;
}

.stButton > button:hover {
    background-color: #f40612;
}

.hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 80px 40px;
    margin-bottom: 50px;
    border-radius: 15px;
    text-align: center;
    color: white;
}

.hero-title {
    font-size: 48px;
    font-weight: 900;
    margin-bottom: 20px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.hero-subtitle {
    font-size: 20px;
    opacity: 0.9;
    margin-bottom: 30px;
}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# --------------------------
# BOOK COVER FUNCTION
# --------------------------
def get_book_cover(title, row=None):
    """Get book cover from dataset first, then API as fallback"""
    # First try to get image from the dataset row
    if row is not None and 'imageURL' in row.index and pd.notna(row['imageURL']) and row['imageURL'].strip():
        img_url = str(row['imageURL']).strip()
        if img_url and img_url != 'nan' and 'http' in img_url:
            return img_url

    # Fallback to Google Books API
    try:
        # Clean the title for better API results
        clean_title = title.split(':')[0].split('(')[0].strip()[:50]
        url = f"https://www.googleapis.com/books/v1/volumes?q={clean_title}&maxResults=1"

        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if 'items' in data and len(data['items']) > 0:
            volume_info = data['items'][0].get('volumeInfo', {})
            image_links = volume_info.get('imageLinks', {})

            # Try different image sizes in order of preference
            for size in ['large', 'medium', 'small', 'thumbnail']:
                if size in image_links:
                    return image_links[size]

            # If no specific size, try thumbnail
            if 'thumbnail' in image_links:
                return image_links['thumbnail']

    except Exception as e:
        # Log the error but don't crash
        print(f"Error getting cover for '{title}': {e}")
        pass

    # Multiple fallback options
    fallbacks = [
        "https://via.placeholder.com/200x300/e50914/ffffff?text=No+Cover",
        "https://via.placeholder.com/200x300/667eea/ffffff?text=Book",
        "https://via.placeholder.com/200x300/764ba2/ffffff?text=📚"
    ]

    # Return a random fallback to add variety
    import random
    return random.choice(fallbacks)

# --------------------------
# LOAD DATA
# --------------------------
df = load_and_clean_data()
embeddings = get_embeddings(df['content'].tolist())

# --------------------------
# HERO SECTION
# --------------------------
st.markdown("""
<div class="hero-section">
    <div class="hero-title">📚 BookFlix</div>
    <div class="hero-subtitle">Discover your next favorite book with AI-powered recommendations</div>
</div>
""", unsafe_allow_html=True)

# --------------------------
# SEARCH SECTION
# --------------------------
st.markdown('<div class="search-container">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown('<div class="search-input">', unsafe_allow_html=True)
    book = st.selectbox(
        "🔍 Search for a book to get recommendations",
        df['title'],
        label_visibility="collapsed",
        key="search"
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# TRENDING BOOKS ROW
# --------------------------
st.markdown('<div class="row-title">🔥 Trending Books</div>', unsafe_allow_html=True)

# Create a scrollable row
trending_books = df.sample(20, random_state=42)

cols = st.columns(6)
for i, (_, row) in enumerate(trending_books.iterrows()):
    if i >= 18:  # Show 18 books in 3 rows of 6
        break
    with cols[i % 6]:
        img_url = get_book_cover(row['title'], row)
        st.markdown(f"""
        <div class="book-card">
            <img src="{img_url}"
                 style="width:100%; height:200px; object-fit:cover; border-radius:8px; background-color:#333;"
                 onerror="this.src='https://via.placeholder.com/200x300/333/666?text=Loading...'"
                 loading="lazy">
            <div class="book-title">{row['title'][:50]}{'...' if len(row['title']) > 50 else ''}</div>
        </div>
        """, unsafe_allow_html=True)

# --------------------------
# RECOMMENDATIONS SECTION
# --------------------------
if st.button("🎯 Get Recommendations", key="recommend_btn"):
    st.markdown('<div class="row-title">✨ Recommended for You</div>', unsafe_allow_html=True)

    idx = df[df['title'] == book].index[0]

    recs = recommend_books(
        embeddings[idx],
        embeddings,
        df
    )

    cols = st.columns(6)
    for i, (title, score) in enumerate(recs):
        if i >= 12:  # Show top 12 recommendations
            break
        # Get the full row data for this recommended book
        rec_row = df[df['title'] == title].iloc[0] if len(df[df['title'] == title]) > 0 else None
        with cols[i % 6]:
            img_url = get_book_cover(title, rec_row)
            st.markdown(f"""
            <div class="book-card">
                <img src="{img_url}"
                     style="width:100%; height:200px; object-fit:cover; border-radius:8px; background-color:#333;"
                     onerror="this.src='https://via.placeholder.com/200x300/333/666?text=Loading...'"
                     loading="lazy">
                <div class="book-title">{title[:50]}{'...' if len(title) > 50 else ''}</div>
            </div>
            """, unsafe_allow_html=True)

# --------------------------
# POPULAR GENRES ROW
# --------------------------
st.markdown('<div class="row-title">📖 Popular Genres</div>', unsafe_allow_html=True)

# Sample some books from different "genres" (we'll simulate this)
genre_books = df.sample(12, random_state=123)

cols = st.columns(6)
for i, (_, row) in enumerate(genre_books.iterrows()):
    with cols[i % 6]:
        img_url = get_book_cover(row['title'], row)
        st.markdown(f"""
        <div class="book-card">
            <img src="{img_url}"
                 style="width:100%; height:200px; object-fit:cover; border-radius:8px; background-color:#333;"
                 onerror="this.src='https://via.placeholder.com/200x300/333/666?text=Loading...'"
                 loading="lazy">
            <div class="book-title">{row['title'][:50]}{'...' if len(row['title']) > 50 else ''}</div>
        </div>
        """, unsafe_allow_html=True)