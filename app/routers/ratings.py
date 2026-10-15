from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.cache import cache
from app.database import get_db
from app.deps import get_current_user
from app.models import Movie, Rating, User
from app.schemas import RatingIn, RatingOut, RatingUpdate

router = APIRouter(prefix="/api/ratings", tags=["ratings"])


@router.post("", response_model=RatingOut, status_code=201)
def create_rating(body: RatingIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not db.get(Movie, body.movie_id):
        raise HTTPException(404, "Movie not found")
    if db.query(Rating).filter_by(user_id=user.id, movie_id=body.movie_id).first():
        raise HTTPException(409, "Already rated; use PUT /api/ratings/{id} to update")
    rating = Rating(user_id=user.id, movie_id=body.movie_id, rating=body.rating)
    db.add(rating)
    db.commit()
    db.refresh(rating)
    cache.clear()  # recommendations depend on ratings
    return rating


@router.put("/{rating_id}", response_model=RatingOut)
def update_rating(rating_id: int, body: RatingUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rating = db.query(Rating).filter_by(id=rating_id, user_id=user.id).first()
    if not rating:
        raise HTTPException(404, "Rating not found")
    rating.rating = body.rating
    db.commit()
    db.refresh(rating)
    cache.clear()
    return rating
