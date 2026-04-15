import pandas as pd
from pathlib import Path
import os

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
    - Try current working directory as fallback
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

    # Additional fallback: try current working directory
    cwd = Path.cwd()
    for name in preferred_names:
        candidate = cwd / "data" / "Good reads dataset" / name
        if candidate.exists():
            return candidate
        candidate2 = cwd / "data" / name
        if candidate2.exists():
            return candidate2

    # Final fallback: search from current working directory
    files = list(cwd.rglob("*.csv"))
    if files:
        return files[0]

    raise FileNotFoundError(f"No CSV file found in {search_dir} or {cwd}. Put your dataset under data/ or data/Good reads dataset/")


def load_and_clean_data(path: str | Path | None = None):
    """Load and clean the CSV. If `path` is None it will be auto-detected.

    Returns a cleaned DataFrame with a `content` column for semantic analysis.
    """
    try:
        if path is None:
            path = find_csv()
        path = Path(path)

        print(f"Loading CSV from: {path}")
        print(f"File exists: {path.exists()}")
        print(f"File size: {path.stat().st_size if path.exists() else 'N/A'} bytes")

        # Try to read the CSV with error handling
        try:
            df = pd.read_csv(path, encoding='utf-8')
        except UnicodeDecodeError:
            # Try different encoding
            df = pd.read_csv(path, encoding='latin1')
        except Exception as e:
            raise Exception(f"Failed to read CSV file: {e}")

        print(f"Successfully loaded DataFrame with shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")

        if df.empty:
            raise ValueError("CSV file is empty or has no valid data")

        # Check if required columns exist
        required_cols = ["title", "author", "description"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"Warning: Missing columns {missing_cols}. Available columns: {list(df.columns)}")
            # Try to map alternative column names
            column_mapping = {
                "book_title": "title",
                "book_author": "author",
                "summary": "description",
                "text": "description"
            }
            for alt, std in column_mapping.items():
                if alt in df.columns and std in missing_cols:
                    df = df.rename(columns={alt: std})
                    missing_cols.remove(std)

            if missing_cols:
                raise ValueError(f"Required columns still missing: {missing_cols}")

        # Keep important columns (include those needed for filtering and display)
        columns_to_keep = ["title", "author", "description"]
        optional_columns = ["rating", "pages", "imageURL", "ratings", "genres"]

        # Add optional columns if they exist
        for col in optional_columns:
            if col in df.columns:
                columns_to_keep.append(col)

        df = df[columns_to_keep]

        # Fill missing values
        df["description"] = df["description"].fillna("")
        if "rating" in df.columns:
            df["rating"] = pd.to_numeric(df["rating"], errors='coerce').fillna(0.0)
        if "pages" in df.columns:
            df["pages"] = pd.to_numeric(df["pages"], errors='coerce').fillna(0)
        if "ratings" in df.columns:
            df["ratings"] = pd.to_numeric(df["ratings"], errors='coerce').fillna(0)

        # Remove duplicates
        df = df.drop_duplicates(subset="title")

        # Reset index
        df = df.reset_index(drop=True)

        # Combine text for semantic analysis
        df["content"] = df["title"] + " " + df["author"] + " " + df["description"]

        # Remove duplicates
        df = df.drop_duplicates(subset="title")

        # Reset index
        df = df.reset_index(drop=True)

        # Combine text for semantic analysis
        df["content"] = df["title"] + " " + df["author"] + " " + df["description"]

        print(f"Final DataFrame shape: {df.shape}")
        print("Sample data:")
        print(df.head())

        return df

    except Exception as e:
        print(f"Error in load_and_clean_data: {e}")
        raise


# Example usage: auto-detect the dataset in the `data` folder next to this file
if __name__ == "__main__":
    df = load_and_clean_data()