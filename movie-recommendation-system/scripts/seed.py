"""Usage: python -m scripts.seed [path/to/movies.csv]  (re-creates the movies table contents)"""
import sys

from app.config import SAMPLE_CSV
from app.database import Base, SessionLocal, engine
from app.models import Movie
from app.seed import load_movies_csv

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else SAMPLE_CSV
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.query(Movie).delete()
        db.commit()
        print(f"Loaded {load_movies_csv(db, path)} movies from {path}")
