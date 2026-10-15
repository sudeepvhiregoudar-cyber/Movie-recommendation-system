"""Recommendation orchestration: content, collaborative, hybrid, popular and trending."""
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.cache import cache
from app.ml.collaborative import CollaborativeModel
from app.ml.content import ContentModel
from app.models import Movie, Rating
from app.schemas import MovieOut

HYBRID_ALPHA = 0.6  # weight of collaborative filtering vs content in the hybrid score


def _pack(movie, score):
    return {"movie": MovieOut.model_validate(movie).model_dump(), "score": round(float(score), 4)}


def content_model(db: Session) -> ContentModel:
    return cache.get_or_set("content_model", lambda: ContentModel().fit(db.query(Movie).all()))


def cf_model(db: Session) -> CollaborativeModel:
    def build():
        rows = db.query(Rating.user_id, Rating.movie_id, Rating.rating).all()
        df = pd.DataFrame([tuple(r) for r in rows], columns=["user_id", "movie_id", "rating"])
        return CollaborativeModel().fit(df)
    return cache.get_or_set("cf_model", build)


def _movies_by_id(db, ids):
    return {m.id: m for m in db.query(Movie).filter(Movie.id.in_(list(ids)))}


def similar_movies(db: Session, movie_id: int, n: int = 10):
    def build():
        pairs = content_model(db).similar(movie_id, n)
        movies = _movies_by_id(db, [i for i, _ in pairs])
        return [_pack(movies[i], s) for i, s in pairs]
    return cache.get_or_set(("similar", movie_id, n), build)


def popular(db: Session, n: int = 10):
    """IMDB-style weighted rating so a 9.0 from 3 votes doesn't beat an 8.4 from 30,000."""
    def build():
        movies = db.query(Movie).all()
        if not movies:
            return []
        r = np.array([m.vote_average for m in movies])
        v = np.array([m.vote_count for m in movies], dtype=float)
        c, m_ = r.mean(), np.percentile(v, 50)
        wr = v / (v + m_ + 1e-9) * r + m_ / (v + m_ + 1e-9) * c
        order = np.argsort(wr)[::-1][:n]
        return [_pack(movies[i], wr[i]) for i in order]
    return cache.get_or_set(("popular", n), build)


def trending(db: Session, n: int = 10):
    """Catalogue popularity boosted by how many ratings arrived in the last 30 days."""
    def build():
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        rows = (
            db.query(Movie, func.count(Rating.id))
            .outerjoin(Rating, and_(Rating.movie_id == Movie.id, Rating.created_at >= cutoff))
            .group_by(Movie.id).all()
        )
        scored = sorted(((m.popularity + 10 * c, m) for m, c in rows), key=lambda t: t[0], reverse=True)
        return [_pack(m, s) for s, m in scored[:n]]
    return cache.get_or_set(("trending", n), build)


def user_recommendations(db: Session, user_id: int, n: int = 10):
    """Hybrid: blend CF predictions with similarity to the user's liked movies. Returns (strategy, results)."""
    def build():
        ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
        if not ratings:
            return "popular_fallback", popular(db, n)  # cold start
        rated = {r.movie_id: r.rating for r in ratings}
        content = content_model(db)
        liked = {m: r - 2.5 for m, r in rated.items() if r >= 3.5}
        cscore = content.profile_scores(liked)
        cnorm = cscore / cscore.max() if cscore.max() > 0 else cscore

        cf_item = cf_model(db).predict(user_id, "item")
        cf_user = cf_model(db).predict(user_id, "user")
        cf = {m: (cf_item.get(m, np.nan) + cf_user.get(m, np.nan)) / 2
              if m in cf_item and m in cf_user else cf_item.get(m, cf_user.get(m, np.nan))
              for m in set(cf_item) | set(cf_user)}
        cfnorm = np.array([(cf.get(i, np.nan) - 0.5) / 4.5 for i in content.ids])

        final = np.where(np.isnan(cfnorm), cnorm, HYBRID_ALPHA * cfnorm + (1 - HYBRID_ALPHA) * cnorm)
        order = [i for i in np.argsort(final)[::-1] if content.ids[i] not in rated and final[i] > 0][:n]
        movies = _movies_by_id(db, [content.ids[i] for i in order])
        return "hybrid", [_pack(movies[content.ids[i]], final[i]) for i in order]
    return cache.get_or_set(("user", user_id, n), build)
