import os

os.environ["DATABASE_URL"] = "sqlite:///./test_movies.db"
if os.path.exists("test_movies.db"):
    os.remove("test_movies.db")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def signup(client, name):
    body = {"username": name, "email": f"{name}@example.com", "password": "secret123"}
    assert client.post("/api/auth/register", json=body).status_code == 201
    token = client.post("/api/auth/login", json={"username": name, "password": "secret123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_movies_and_search(client):
    r = client.get("/api/movies?limit=5")
    assert r.status_code == 200 and len(r.json()["items"]) == 5 and r.json()["total"] >= 20
    assert client.get("/api/movies/search?q=nolan").json()["total"] == 3
    assert client.get("/api/movies/1").json()["title"]
    assert client.get("/api/movies/99999").status_code == 404
    assert client.get("/api/movies?limit=0").status_code == 422


def test_auth_errors(client):
    assert client.get("/api/users/profile").status_code == 401
    assert client.get("/api/users/profile", headers={"Authorization": "Bearer junk"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "nobody", "password": "x"}).status_code == 401
    h = signup(client, "dup")
    assert client.get("/api/users/profile", headers=h).json()["username"] == "dup"
    dup = {"username": "dup", "email": "other@example.com", "password": "secret123"}
    assert client.post("/api/auth/register", json=dup).status_code == 409


def test_content_recommendations(client):
    r = client.get("/api/recommendations/movie/1?n=3")
    assert r.status_code == 200 and r.json()["count"] == 3
    assert client.get("/api/recommendations/1?n=3").status_code == 200  # Phase 1 path
    assert client.get("/api/recommendations/movie/99999").status_code == 404


def test_ratings_and_personalised(client):
    a, b = signup(client, "alice"), signup(client, "bob")
    uid = client.get("/api/users/profile", headers=a).json()["id"]
    for mid, ra, rb in [(1, 5, 5), (2, 4.5, 4.5), (3, 4, 4), (13, 1, 1.5)]:
        assert client.post("/api/ratings", json={"movie_id": mid, "rating": ra}, headers=a).status_code == 201
        client.post("/api/ratings", json={"movie_id": mid, "rating": rb}, headers=b)
    client.post("/api/ratings", json={"movie_id": 4, "rating": 5}, headers=b)

    assert client.post("/api/ratings", json={"movie_id": 1, "rating": 3}, headers=a).status_code == 409
    assert client.post("/api/ratings", json={"movie_id": 1, "rating": 9}, headers=a).status_code == 422
    assert client.post("/api/ratings", json={"movie_id": 999, "rating": 3}, headers=a).status_code == 404

    history = client.get("/api/users/ratings", headers=a).json()
    assert len(history) == 4
    assert client.put(f"/api/ratings/{history[0]['id']}", json={"rating": 3}, headers=a).json()["rating"] == 3
    assert client.put(f"/api/ratings/{history[0]['id']}", json={"rating": 3}, headers=b).status_code == 404

    r = client.get(f"/api/recommendations/user/{uid}", headers=a)
    assert r.status_code == 200 and r.json()["strategy"] == "hybrid"
    rated = {1, 2, 3, 13}
    assert all(x["movie"]["id"] not in rated for x in r.json()["results"])
    assert client.get("/api/recommendations/user/999", headers=a).status_code == 403
    assert client.get(f"/api/recommendations/user/{uid}").status_code == 401


def test_cold_start_trending_popular(client):
    h = signup(client, "newbie")
    uid = client.get("/api/users/profile", headers=h).json()["id"]
    assert client.get(f"/api/recommendations/user/{uid}", headers=h).json()["strategy"] == "popular_fallback"
    assert client.get("/api/recommendations/trending?n=5").json()["count"] == 5
    assert client.get("/api/recommendations/popular?n=5").json()["count"] == 5


def test_frontend_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "Movie Recommendation System" in r.text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/health").json()["status"] == "ok"
