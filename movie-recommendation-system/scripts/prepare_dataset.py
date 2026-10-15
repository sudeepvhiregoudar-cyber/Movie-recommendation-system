"""Convert the Kaggle TMDB 5000 dataset into this project's CSV format.

Usage: python -m scripts.prepare_dataset tmdb_5000_movies.csv tmdb_5000_credits.csv data/movies.csv
Then:  python -m scripts.seed data/movies.csv
"""
import ast
import sys

import pandas as pd

from app.seed import clean_dataframe


def names(raw, key="name", limit=None):
    try:
        items = [d[key] for d in ast.literal_eval(raw)]
    except (ValueError, SyntaxError, TypeError):
        return ""
    return "|".join(items[:limit] if limit else items)


def director(raw):
    try:
        return next((d["name"] for d in ast.literal_eval(raw) if d.get("job") == "Director"), "")
    except (ValueError, SyntaxError, TypeError):
        return ""


if __name__ == "__main__":
    movies_csv, credits_csv, out = sys.argv[1:4]
    movies = pd.read_csv(movies_csv)
    credits = pd.read_csv(credits_csv).rename(columns={"movie_id": "id"})[["id", "cast", "crew"]]
    df = movies.merge(credits, on="id")
    df["genres"] = df["genres"].apply(names)
    df["keywords"] = df["keywords"].apply(names)
    df["cast_names"] = df["cast"].apply(lambda s: names(s, limit=5))
    df["director"] = df["crew"].apply(director)
    clean_dataframe(df).to_csv(out, index=False)
    print(f"Wrote {out}")
