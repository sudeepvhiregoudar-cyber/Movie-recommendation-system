from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    genres: Optional[str] = ""
    overview: Optional[str] = ""
    cast_names: Optional[str] = ""
    director: Optional[str] = ""
    keywords: Optional[str] = ""
    release_date: Optional[str] = ""
    vote_average: float = 0.0
    vote_count: int = 0
    popularity: float = 0.0


class MovieList(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[MovieOut]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(pattern=EMAIL_RE)
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    created_at: Optional[datetime] = None


class ProfileUpdate(BaseModel):
    email: str = Field(pattern=EMAIL_RE)


class RatingIn(BaseModel):
    movie_id: int
    rating: float = Field(ge=0.5, le=5.0)


class RatingUpdate(BaseModel):
    rating: float = Field(ge=0.5, le=5.0)


class RatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    movie_id: int
    rating: float
    created_at: Optional[datetime] = None


class RecommendationOut(BaseModel):
    movie: MovieOut
    score: float


class RecommendationResponse(BaseModel):
    strategy: str
    count: int
    results: List[RecommendationOut]
