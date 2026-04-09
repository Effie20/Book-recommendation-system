import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def evaluate_model(test_embeddings, train_embeddings):
    scores = []

    for i in range(len(test_embeddings)):
        similarities = cosine_similarity(
            [test_embeddings[i]],
            train_embeddings
        )[0]

        scores.append(max(similarities))

    return np.mean(scores)