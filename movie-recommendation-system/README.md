# Movie Recommendation System (FastAPI + scikit-learn)

Full-stack app (FastAPI backend + responsive web UI) that recommends movies using **content-based**, **collaborative (item- and user-based)** and **hybrid** filtering, with JWT auth, ratings, caching and Swagger docs.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # set SECRET_KEY, DATABASE_URL
uvicorn app.main:app --reload
```
Open http://localhost:8000 for the web app (browse, search, sign up, rate, get recommendations) and http://localhost:8000/docs for Swagger UI. On first start the 25-movie sample in `data/movies_sample.csv` is loaded automatically.

## Use the real dataset (TMDB 5000 from Kaggle)
```bash
python -m scripts.prepare_dataset tmdb_5000_movies.csv tmdb_5000_credits.csv data/movies.csv
python -m scripts.eda data/movies.csv        # Phase 1 EDA: counts, genres, ratings, missing/duplicates
python -m scripts.seed data/movies.csv
```

## Endpoints
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | /api/auth/register | – | Create account |
| POST | /api/auth/login | – | Returns JWT (`Authorization: Bearer <token>`) |
| GET / PUT | /api/users/profile | ✔ | View / update profile |
| GET | /api/users/ratings | ✔ | Rating history |
| GET | /api/movies?skip&limit&genre | – | List movies |
| GET | /api/movies/search?q= | – | Search title, director, cast, keywords |
| GET | /api/movies/{id} | – | Movie details |
| POST | /api/ratings | ✔ | Rate a movie (0.5–5) |
| PUT | /api/ratings/{id} | ✔ | Update own rating |
| GET | /api/recommendations/movie/{id} | – | Similar movies (also `/api/recommendations/{id}`) |
| GET | /api/recommendations/user/{user_id} | ✔ | Hybrid personalised picks (own id only) |
| GET | /api/recommendations/trending | – | Popularity + recent rating activity |
| GET | /api/recommendations/popular | – | IMDB-style weighted rating |

Errors are JSON: `{"detail": "..."}` with 401/403/404/409/422/500.

## How recommendations work
- **Content-based** (`app/ml/content.py`): TF-IDF over genres, keywords, cast, director, overview; cosine similarity.
- **Collaborative** (`app/ml/collaborative.py`): mean-centred ratings; item-based and user-based predictions.
- **Hybrid** (`app/services.py`): `0.6 * CF + 0.4 * content` (content built from movies the user rated ≥ 3.5). New users with no ratings fall back to popular movies.
- **Performance**: results and fitted models are cached in memory (`CACHE_TTL`, cleared whenever ratings change); indexes on title, user_id, movie_id.

## Tests
```bash
pytest -q
```
Postman: import `http://localhost:8000/openapi.json` as a collection.

## Deploy (Render / Railway / any Docker host)
1. Push to GitHub. Create a PostgreSQL instance and a web service from this repo (Dockerfile included).
2. Set env vars: `DATABASE_URL`, `SECRET_KEY` (long random), optionally `CACHE_TTL`.
3. Deploy, open `<your-url>/docs`, and submit that live URL with Phase 2.

## Structure
```
app/            main.py, models, schemas, auth, services, routers/, ml/
data/           movies_sample.csv
scripts/        prepare_dataset.py, eda.py, seed.py
frontend/       index.html, styles.css, app.js (served by FastAPI at /)
tests/          test_api.py
```
