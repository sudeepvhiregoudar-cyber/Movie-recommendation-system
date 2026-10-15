import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.config import AUTO_SEED, SAMPLE_CSV
from app.database import Base, SessionLocal, engine
from app.models import Movie
from app.routers import auth, movies, ratings, recommendations, users
from app.seed import load_movies_csv

log = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if AUTO_SEED:
        with SessionLocal() as db:
            if db.query(Movie).count() == 0:
                log.info("Seeded %d movies", load_movies_csv(db, SAMPLE_CSV))
    yield


app = FastAPI(
    title="Movie Recommendation System API",
    description="Content-based, collaborative and hybrid movie recommendations.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

for r in (auth.router, users.router, movies.router, ratings.router, recommendations.router):
    app.include_router(r)


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError):
    log.exception("Database error")
    return JSONResponse(status_code=500, content={"detail": "Database error"})


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "docs": "/docs"}
