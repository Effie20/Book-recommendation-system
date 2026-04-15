import pandas as pd
from pathlib import Path
import os

# Auto-detect CSV in the repository `data` folder
# Try multiple strategies for different environments (local vs Streamlit Cloud)
def get_base_paths():
    """Get possible base paths for the data directory"""
    paths = []

    # Strategy 1: Relative to this file (works locally)
    try:
        file_based = Path(__file__).resolve().parent
        paths.append(file_based)
    except:
        pass

    # Strategy 2: Current working directory (works on Streamlit Cloud)
    try:
        cwd_based = Path.cwd()
        paths.append(cwd_based)
        paths.append(cwd_based / "data")
    except:
        pass

    # Strategy 3: Parent of current working directory
    try:
        parent_cwd = Path.cwd().parent
        paths.append(parent_cwd)
        paths.append(parent_cwd / "data")
    except:
        pass

    return paths

PREFERRED_FILES = [
    "cleaned_goodreads_books_dataset.csv",
    "goodreads_books_dataset.csv",
]


def find_csv(preferred_names=PREFERRED_FILES, search_paths=None):
    """Return a Path to a CSV file.

    Strategy:
    - Look for preferred filenames in multiple possible locations
    - Try current directory and subdirectories
    - Raise FileNotFoundError if none exist
    """
    if search_paths is None:
        search_paths = get_base_paths()

    print(f"Searching for CSV files in paths: {[str(p) for p in search_paths]}")

    # Check preferred locations first
    for base_path in search_paths:
        for name in preferred_names:
            candidate = base_path / "Good reads dataset" / name
            print(f"Checking: {candidate}")
            if candidate.exists():
                print(f"Found CSV at: {candidate}")
                return candidate
            candidate2 = base_path / name
            print(f"Checking: {candidate2}")
            if candidate2.exists():
                print(f"Found CSV at: {candidate2}")
                return candidate2

    # Fallback: search recursively from search paths
    for base_path in search_paths:
        if base_path.exists():
            files = list(base_path.rglob("*.csv"))
            if files:
                print(f"Found CSV via recursive search: {files[0]}")
                return files[0]

    # Final fallback: search from current directory
    try:
        cwd = Path.cwd()
        files = list(cwd.rglob("*.csv"))
        if files:
            print(f"Found CSV via CWD recursive search: {files[0]}")
            return files[0]
    except:
        pass

    available_paths = [str(p) for p in search_paths if p.exists()]
    raise FileNotFoundError(f"No CSV file found. Searched in: {available_paths}")


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