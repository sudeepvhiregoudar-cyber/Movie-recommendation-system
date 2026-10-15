from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Rating, User
from app.schemas import ProfileUpdate, RatingOut, UserOut

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/profile", response_model=UserOut)
def get_profile(user: User = Depends(get_current_user)):
    return user


@router.put("/profile", response_model=UserOut)
def update_profile(body: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email, User.id != user.id).first():
        raise HTTPException(409, "Email already in use")
    user.email = body.email
    db.commit()
    db.refresh(user)
    return user


@router.get("/ratings", response_model=List[RatingOut])
def rating_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Rating).filter(Rating.user_id == user.id).order_by(Rating.created_at.desc()).all()
