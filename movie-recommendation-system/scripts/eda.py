"""Usage: python -m scripts.eda [movies.csv]  - prints the Phase 1 exploratory data analysis."""
import sys

import pandas as pd

from app.config import SAMPLE_CSV

df = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else SAMPLE_CSV)
print(f"Movies: {len(df)}")
print(f"Duplicate title+date rows: {df.duplicated(['title', 'release_date']).sum()}")
print("\nMissing values per column:\n", df.isna().sum().to_string())
print("\nTop genres:\n", df["genres"].dropna().str.split("|").explode().value_counts().head(10).to_string())
print("\nRating distribution (vote_average):\n", df["vote_average"].describe().round(2).to_string())
print("\nVote-count buckets:\n", pd.cut(df["vote_count"], [-1, 100, 1000, 10000, 10**9],
      labels=["<100", "100-1k", "1k-10k", ">10k"]).value_counts().sort_index().to_string())
print("\nFeatures used for recommendations: genres, keywords, cast_names, director, overview")
