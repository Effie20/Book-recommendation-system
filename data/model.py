from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_vectorizer = None

def get_embeddings(text_data):
    global _vectorizer
    _vectorizer = TfidfVectorizer(stop_words="english", max_features=10000)
    embeddings = _vectorizer.fit_transform(text_data)
    return embeddings

def recommend_books(test_embedding, train_embeddings, train_df, top_n=5):
    similarities = cosine_similarity(test_embedding, train_embeddings)[0]
    top_indices = similarities.argsort()[-top_n:][::-1]

    results = []
    for idx in top_indices:
        results.append((train_df.iloc[idx]['title'], float(similarities[idx])))

    return results
