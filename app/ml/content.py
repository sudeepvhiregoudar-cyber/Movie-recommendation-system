"""Content-based filtering: TF-IDF over genres, keywords, cast, director and overview."""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


def _tokens(pipe_string):
    # "Christopher Nolan|Hans Zimmer" -> "christophernolan hanszimmer"
    return " ".join(t.replace(" ", "").lower() for t in (pipe_string or "").split("|") if t)


def build_soup(movie) -> str:
    # genres and director are repeated to weight them more heavily
    parts = [
        _tokens(movie.genres), _tokens(movie.genres),
        _tokens(movie.keywords), _tokens(movie.cast_names),
        _tokens(movie.director), _tokens(movie.director),
        movie.overview or "",
    ]
    return " ".join(parts)


class ContentModel:
    def fit(self, movies):
        self.ids = [m.id for m in movies]
        self.index = {mid: i for i, mid in enumerate(self.ids)}
        if not movies:
            self.matrix = None
            return self
        self.matrix = TfidfVectorizer(stop_words="english").fit_transform(build_soup(m) for m in movies)
        return self

    def similar(self, movie_id, n=10):
        """Top-n (movie_id, cosine_similarity) pairs most similar to movie_id."""
        i = self.index.get(movie_id)
        if i is None or self.matrix is None:
            return []
        sims = linear_kernel(self.matrix[i], self.matrix).ravel()
        sims[i] = -1.0
        top = np.argsort(sims)[::-1][:n]
        return [(self.ids[j], float(sims[j])) for j in top if sims[j] > 0]

    def profile_scores(self, weights):
        """Weighted average similarity of every movie to the movies in `weights` ({movie_id: weight})."""
        idx = [self.index[m] for m in weights if m in self.index]
        if not idx or self.matrix is None:
            return np.zeros(len(self.ids))
        w = np.array([weights[self.ids[i]] for i in idx], dtype=float)
        sims = linear_kernel(self.matrix[idx], self.matrix)
        return (w[:, None] * sims).sum(axis=0) / w.sum()
