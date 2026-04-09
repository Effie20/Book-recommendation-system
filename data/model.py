from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embeddings(text_data):
    return model.encode(text_data, show_progress_bar=True)

def compute_similarity(embeddings):
    return cosine_similarity(embeddings)

def recommend_books(test_embedding, train_embeddings, train_df, top_n=5):
    similarities = cosine_similarity([test_embedding], train_embeddings)[0]
    top_indices = similarities.argsort()[-top_n:][::-1]

    results = []
    for idx in top_indices:
        results.append((train_df.iloc[idx]['title'], similarities[idx]))

    return results
