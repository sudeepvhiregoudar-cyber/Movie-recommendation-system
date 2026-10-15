from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Movie
from app.schemas import MovieList, MovieOut

router = APIRouter(prefix="/api/movies", tags=["movies"])


@router.get("", response_model=MovieList)
def list_movies(
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    genre: Optional[str] = None, db: Session = Depends(get_db),
):
    q = db.query(Movie)
    if genre:
        q = q.filter(Movie.genres.ilike(f"%{genre}%"))
    return {"total": q.count(), "skip": skip, "limit": limit, "items": q.order_by(Movie.id).offset(skip).limit(limit).all()}


@router.get("/search", response_model=MovieList)
def search_movies(
    q: str = Query(..., min_length=1), skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db),
):
    like = f"%{q}%"
    query = db.query(Movie).filter(or_(
        Movie.title.ilike(like), Movie.director.ilike(like),
        Movie.cast_names.ilike(like), Movie.keywords.ilike(like),
    ))
    return {"total": query.count(), "skip": skip, "limit": limit, "items": query.offset(skip).limit(limit).all()}


@router.get("/{movie_id}", response_model=MovieOut)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    return movie
