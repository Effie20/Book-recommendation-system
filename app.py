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
    background-color: #000000;
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
    border: 3px solid #ff69b4;
    background-color: rgba(255, 20, 147, 0.1);
}

.book-card:hover {
    transform: scale(1.05);
    box-shadow: 0 8px 25px rgba(0,0,0,0.5);
}

.book-title {
    font-size: 14px;
    font-weight: 700;
    text-align: center;
    margin-top: 8px;
    color: black;
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
    background-color: #8a2be2;
    border: 2px solid #9370db;
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

.hero-stats {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 30px;
}

.stat-item {
    text-align: center;
    color: white;
}

.stat-number {
    font-size: 28px;
    font-weight: 900;
    margin-bottom: 5px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.stat-label {
    font-size: 14px;
    opacity: 0.9;
    font-weight: 500;
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
    if row is not None and 'imageURL' in row.index:
        img_url = str(row['imageURL']).strip()
        print(f"DEBUG: Checking imageURL for '{title}': '{img_url}'")  # Debug line
        if pd.notna(row['imageURL']) and img_url and img_url != 'nan' and 'http' in img_url.lower():
            print(f"DEBUG: Using dataset image: {img_url}")  # Debug line
            return img_url

    print(f"DEBUG: No valid dataset image for '{title}', trying API")  # Debug line
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
                    print(f"DEBUG: Using API image ({size}): {image_links[size]}")  # Debug line
                    return image_links[size]

            # If no specific size, try thumbnail
            if 'thumbnail' in image_links:
                print(f"DEBUG: Using API thumbnail: {image_links['thumbnail']}")  # Debug line
                return image_links['thumbnail']

    except Exception as e:
        print(f"DEBUG: API error for '{title}': {e}")  # Debug line
        pass

    # Multiple fallback options
    fallbacks = [
        "https://via.placeholder.com/200x300/e50914/ffffff?text=No+Cover",
        "https://via.placeholder.com/200x300/667eea/ffffff?text=Book",
        "https://via.placeholder.com/200x300/764ba2/ffffff?text=📚"
    ]

    # Return a random fallback to add variety
    import random
    fallback = random.choice(fallbacks)
    print(f"DEBUG: Using fallback for '{title}': {fallback}")  # Debug line
    return fallback

# --------------------------
# BOOK DETAILS MODAL
# --------------------------
if 'selected_book' not in st.session_state:
    st.session_state.selected_book = None

def show_book_details(book_title):
    """Display detailed information about a selected book"""
    if book_title:
        book_data = df[df['title'] == book_title].iloc[0] if len(df[df['title'] == book_title]) > 0 else None
        if book_data is not None:
            with st.expander(f"{book_title}", expanded=True):
                col1, col2 = st.columns([1, 2])

                with col1:
                    img_url = get_book_cover(book_title, book_data)
                    st.image(img_url, width=200)

                with col2:
                    st.markdown(f"**👤 Author:** {book_data.get('author', 'Unknown')}")
                    st.markdown(f"**📄 Pages:** {book_data.get('pages', 'N/A')}")
                    st.markdown(f"**⭐ Rating:** {book_data.get('rating', 'N/A')}")
                    st.markdown(f"**📊 Ratings:** {book_data.get('ratings', 'N/A')}")

                    # Show description preview
                    desc = book_data.get('description', 'No description available')
                    if len(desc) > 300:
                        desc = desc[:300] + "..."
                    st.markdown(f"**📝 Description:** {desc}")

                    # Add to reading list button
                    if st.button(f"📚 Add '{book_title[:30]}...' to Reading List", key=f"add_{book_title[:20]}"):
                        if 'reading_list' not in st.session_state:
                            st.session_state.reading_list = []
                        if book_title not in st.session_state.reading_list:
                            st.session_state.reading_list.append(book_title)
                            st.success(f"✅ Added '{book_title}' to your reading list!")
                        else:
                            st.info("📖 This book is already in your reading list!")

# Show book details if a book is selected
if st.session_state.selected_book:
    show_book_details(st.session_state.selected_book)

# --------------------------
# HERO SECTION
# --------------------------
st.markdown(f"""
<div class="hero-section">
    <div class="hero-title">📚 BookFlix</div>
    <div class="hero-subtitle">Discover your next favorite book with AI-powered recommendations</div>
    <div class="hero-stats">
        <div class="stat-item">
            <div class="stat-number">{len(df):,}</div>
            <div class="stat-label">Books</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">AI-Powered</div>
            <div class="stat-label">Recommendations</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">Semantic</div>
            <div class="stat-label">Analysis</div>
        </div>
    </div>
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
        " Search for a book to get recommendations",
        df['title'],
        label_visibility="collapsed",
        key="search"
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# ADVANCED SEARCH & FILTERS
# --------------------------
with st.expander("🔍 Advanced Search & Filters", expanded=False):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        min_rating = st.slider("Min Rating", 0.0, 5.0, 0.0, 0.5)
    with col2:
        min_pages = st.slider("Min Pages", 0, 2000, 0, 50)
    with col3:
        max_pages = st.slider("Max Pages", 0, 2000, 1000, 50)
    with col4:
        sort_by = st.selectbox("Sort by", ["title", "rating", "pages", "ratings"])

    # Apply filters
    filtered_df = df[
        (df['rating'] >= min_rating) &
        (df['pages'] >= min_pages) &
        (df['pages'] <= max_pages)
    ].sort_values(sort_by, ascending=False)

    st.write(f"📚 Found {len(filtered_df)} books matching your criteria")

    if len(filtered_df) > 0:
        # Show filtered results
        filter_cols = st.columns(6)
        for i, (_, row) in enumerate(filtered_df.head(12).iterrows()):
            with filter_cols[i % 6]:
                img_url = get_book_cover(row['title'], row)
                if st.button(f"🔍\n{row['title'][:25]}...", key=f"filter_{i}"):
                    st.session_state.selected_book = row['title']
                st.markdown(f"""
                <div class="book-card">
                    <img src="{img_url}" style="width:100%; height:150px; object-fit:cover; border-radius:8px; background-color:#333;" loading="lazy">
                    <div class="book-title" style="font-size: 12px;">{row['title'][:40]}{'...' if len(row['title']) > 40 else ''}</div>
                    <div style="font-size: 10px; color: #888; text-align: center;">⭐ {row['rating']}</div>
                </div>
                """, unsafe_allow_html=True)

# --------------------------
# THEME TOGGLE
# --------------------------
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

# Theme toggle in sidebar
with st.sidebar:
    st.markdown("---")
    theme_col1, theme_col2 = st.columns(2)
    with theme_col1:
        if st.button("🌙 Dark", key="dark_theme", help="Switch to dark theme"):
            st.session_state.theme = 'dark'
            st.rerun()
    with theme_col2:
        if st.button("☀️ Light", key="light_theme", help="Switch to light theme"):
            st.session_state.theme = 'light'
            st.rerun()

# Apply theme
if st.session_state.theme == 'light':
    st.markdown("""
    <style>
    body { background-color: #ffffff; color: #000000; }
    .book-title { color: #000000 !important; }
    .row-title { color: #000000 !important; }
    .hero-section { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    </style>
    """, unsafe_allow_html=True)

# --------------------------
# READING LIST SIDEBAR
# --------------------------
with st.sidebar:
    st.markdown("### 📚 My Reading List")
    if 'reading_list' not in st.session_state or not st.session_state.reading_list:
        st.info("Your reading list is empty. Click 'Add to Reading List' on any book!")
    else:
        for i, book_title in enumerate(st.session_state.reading_list):
            if st.button(f"❌ {book_title[:30]}...", key=f"remove_{i}"):
                st.session_state.reading_list.remove(book_title)
                st.rerun()
        st.markdown(f"**Total books:** {len(st.session_state.reading_list)}")

# --------------------------
# TRENDING BOOKS ROW
# --------------------------
st.markdown('<div class="row-title">Trending Books</div>', unsafe_allow_html=True)

# Create a scrollable row
trending_books = df.sample(20, random_state=42)

cols = st.columns(6)
for i, (_, row) in enumerate(trending_books.iterrows()):
    if i >= 18:  # Show 18 books in 3 rows of 6
        break
    with cols[i % 6]:
        img_url = get_book_cover(row['title'], row)
        # Make book card clickable
        if st.button(f"📖\n{row['title'][:25]}{'...' if len(row['title']) > 25 else ''}",
                    key=f"trending_{i}", help="Click to view details"):
            st.session_state.selected_book = row['title']

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
if st.button("Get Recommendations", key="recommend_btn"):
    if not book:
        st.error("Please select a book first!")
    else:
        with st.spinner("Analyzing book content and finding similar recommendations..."):
            st.markdown('<div class="row-title">Recommended for You</div>', unsafe_allow_html=True)

            # Get the selected book's index
            idx = df[df['title'] == book].index[0]

            # Use semantic analysis to find similar books
            recs = recommend_books(
                embeddings[idx],  # Selected book's embedding
                embeddings,       # All book embeddings
                df               # Book data
            )

            if recs:
                st.success(f"Found {len(recs)} recommendations based on semantic similarity!")

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
                            <div style="font-size: 12px; color: #666; text-align: center; margin-top: 4px;">
                                Similarity: {score:.2f}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("No recommendations found. Try selecting a different book.")
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
# DATA INSIGHTS SECTION
# --------------------------
st.markdown('<div class="row-title">📊 Book Insights</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    # Top rated books
    top_rated = df.nlargest(5, 'rating')[['title', 'rating']]
    with st.expander("⭐ Top Rated Books"):
        for _, book in top_rated.iterrows():
            st.write(f"**{book['title'][:40]}...** - ⭐ {book['rating']}")

with col2:
    # Most popular books (by ratings count)
    most_rated = df.nlargest(5, 'ratings')[['title', 'ratings']]
    with st.expander("📈 Most Popular Books"):
        for _, book in most_rated.iterrows():
            st.write(f"**{book['title'][:40]}...** - 📊 {book['ratings']:,} ratings")

with col3:
    # Reading time distribution
    short_books = len(df[df['pages'] < 200])
    medium_books = len(df[(df['pages'] >= 200) & (df['pages'] < 400)])
    long_books = len(df[df['pages'] >= 400])

    with st.expander("⏱️ Reading Time Distribution"):
        st.write(f"📖 Short (<200 pages): {short_books}")
        st.write(f"📚 Medium (200-400 pages): {medium_books}")
        st.write(f"📝 Long (400+ pages): {long_books}")

# --------------------------
# POPULAR GENRES ROW
# --------------------------
st.markdown('<div class="row-title" style="color: #0066cc;">Popular Genres</div>', unsafe_allow_html=True)

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