"""Load + clean a movies CSV into the database."""
import pandas as pd
from sqlalchemy.orm import Session

from app.models import Movie

COLUMNS = ["title", "genres", "overview", "cast_names", "director", "keywords",
           "release_date", "vote_average", "vote_count", "popularity"]


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={"cast": "cast_names"})
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUMNS].dropna(subset=["title"])
    df = df.drop_duplicates(subset=["title", "release_date"])
    for col in ["genres", "overview", "cast_names", "director", "keywords", "release_date"]:
        df[col] = df[col].fillna("").astype(str)
    for col in ["vote_average", "popularity"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["vote_count"] = pd.to_numeric(df["vote_count"], errors="coerce").fillna(0).astype(int)
    return df.reset_index(drop=True)


def load_movies_csv(db: Session, path: str) -> int:
    df = clean_dataframe(pd.read_csv(path))
    db.bulk_insert_mappings(Movie, df.to_dict("records"))
    db.commit()
    return len(df)
