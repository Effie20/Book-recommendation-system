from data.preprocessing import load_and_clean_data
from data.model import get_embeddings, recommend_books
from sklearn.model_selection import train_test_split

# Load data
df = load_and_clean_data("data/goodreads_books.csv")

# Split data
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# Generate embeddings
train_embeddings = get_embeddings(train_df['content'].tolist())
test_embeddings = get_embeddings(test_df['content'].tolist())

# Test example
for i in range(3):
    print("\nTest Book:", test_df.iloc[i]['title'])

    recs = recommend_books(
        test_embeddings[i],
        train_embeddings,
        train_df
    )

    for title, score in recs:
        print(f"  -> {title} ({score:.2f})")