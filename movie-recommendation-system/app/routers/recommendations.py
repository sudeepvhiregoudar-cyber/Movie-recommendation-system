from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.deps import get_current_user
from app.models import Movie, User
from app.schemas import RecommendationResponse

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])
N = Query(10, ge=1, le=50, description="Number of recommendations")


def _wrap(strategy, results):
    return {"strategy": strategy, "count": len(results), "results": results}


@router.get("/trending", response_model=RecommendationResponse)
def trending(n: int = N, db: Session = Depends(get_db)):
    return _wrap("trending", services.trending(db, n))


@router.get("/popular", response_model=RecommendationResponse)
def popular(n: int = N, db: Session = Depends(get_db)):
    return _wrap("popular", services.popular(db, n))


@router.get("/user/{user_id}", response_model=RecommendationResponse)
def for_user(user_id: int, n: int = N, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.id != user_id:
        raise HTTPException(403, "You can only view your own recommendations")
    strategy, results = services.user_recommendations(db, user_id, n)
    return _wrap(strategy, results)


@router.get("/movie/{movie_id}", response_model=RecommendationResponse)
@router.get("/{movie_id}", response_model=RecommendationResponse, include_in_schema=False)  # Phase 1 path
def for_movie(movie_id: int, n: int = N, db: Session = Depends(get_db)):
    if not db.get(Movie, movie_id):
        raise HTTPException(404, "Movie not found")
    return _wrap("content_based", services.similar_movies(db, movie_id, n))
