"""Collaborative filtering on mean-centred ratings (adjusted cosine), item-based and user-based."""
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


class CollaborativeModel:
    def fit(self, df: pd.DataFrame):
        self.empty = df.empty
        if self.empty:
            return self
        self.piv = df.pivot_table(index="user_id", columns="movie_id", values="rating")
        self.user_mean = self.piv.mean(axis=1)
        self.centered = self.piv.sub(self.user_mean, axis=0).fillna(0.0)
        self.items = list(self.piv.columns)
        self.item_sim = cosine_similarity(self.centered.values.T)
        self.user_sim = cosine_similarity(self.centered.values)
        np.fill_diagonal(self.item_sim, 0.0)
        np.fill_diagonal(self.user_sim, 0.0)
        return self

    def predict(self, user_id, method="item"):
        """Return {movie_id: predicted_rating} for movies the user has not rated yet."""
        if self.empty or user_id not in self.centered.index:
            return {}
        u = self.centered.index.get_loc(user_id)
        observed = ~self.piv.isna().values            # users x items
        rated = observed[u]
        mean = float(self.user_mean.iloc[u])
        c = self.centered.values
        if method == "item":
            num = self.item_sim[:, rated] @ c[u, rated]
            den = np.abs(self.item_sim[:, rated]).sum(axis=1)
        else:  # user-based
            s = self.user_sim[u]
            num = (s[:, None] * c).sum(axis=0)
            den = (np.abs(s)[:, None] * observed).sum(axis=0)
        with np.errstate(divide="ignore", invalid="ignore"):
            delta = np.where(den > 0, num / den, np.nan)
        return {
            m: float(np.clip(mean + d, 0.5, 5.0))
            for m, d, r in zip(self.items, delta, rated)
            if not r and not np.isnan(d)
        }
