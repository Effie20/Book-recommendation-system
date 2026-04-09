import pandas as pd
from pathlib import Path

# Auto-detect CSV in the repository `data` folder (the folder containing this file)
DATA_DIR = Path(__file__).resolve().parent
PREFERRED_FILES = [
    "cleaned_goodreads_books_dataset.csv",
    "goodreads_books_dataset.csv",
]


def find_csv(preferred_names=PREFERRED_FILES, search_dir=DATA_DIR):
    """Return a Path to a CSV file.

    Strategy:
    - Look for preferred filenames in `data/Good reads dataset/` and `data/`
    - If none found, return the first CSV discovered under `data/`
    - Raise FileNotFoundError if none exist
    """
    # Check preferred locations first
    for name in preferred_names:
        candidate = search_dir / "Good reads dataset" / name
        if candidate.exists():
            return candidate
        candidate2 = search_dir / name
        if candidate2.exists():
            return candidate2

    # Fallback: search for any CSV recursively
    files = list(search_dir.rglob("*.csv"))
    if files:
        return files[0]

    raise FileNotFoundError(f"No CSV file found in {search_dir}. Put your dataset under {search_dir} or pass a path.")


def load_and_clean_data(path: str | Path | None = None):
    """Load and clean the CSV. If `path` is None it will be auto-detected.

    Returns a cleaned DataFrame with a `content` column for semantic analysis.
    """
    if path is None:
        path = find_csv()
    path = Path(path)

    print(f"Loading CSV from: {path}")
    df = pd.read_csv(path)

    print(df.head())
    print(df.columns)

    # Keep only important columns
    df = df[["title", "author", "description"]]

    # Fill missing values
    df["description"] = df["description"].fillna("")

    # Remove duplicates
    df = df.drop_duplicates(subset="title")

    # Reset index
    df = df.reset_index(drop=True)

    # Combine text for semantic analysis
    df["content"] = df["title"] + " " + df["author"] + " " + df["description"]

    print(df.head())
    return df


# Example usage: auto-detect the dataset in the `data` folder next to this file
if __name__ == "__main__":
    df = load_and_clean_data()