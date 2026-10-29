"""
ISVM predictor (Xu et al., IEEE TEVC 26(4), 2022, Algorithm 2): an RBF-SVM that labels solutions as
"optimal-looking", updated every environment and used to filter random points into an initial population.
"""

import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC

# The paper grid-searches C and gamma in [2^-5, 2^5]
GRID = 2.0 ** np.arange(-5, 6, 2)


class ISVMPredictor:
    """RBF-SVM carried across environments, working in the unit cube.

    Incremental learning by support-vector carry-over: each update retrains on the previous model's
    support vectors plus the new samples (Syed et al., 1999). This stands in for the exact
    Cauwenberghs–Poggio update used in the paper. history=False rebuilds the SVM from the newest
    samples only (the paper's "SVM" ablation). C and gamma are grid-searched on the first update
    unless given.
    """

    def __init__(self, history=True, C=None, gamma=None):
        self.history, self.C, self.gamma = history, C, gamma
        self.svm = None
        self.X = self.y = None

    def update(self, X, y):
        if self.history and self.svm is not None:
            X, y = np.vstack([self.X, X]), np.r_[self.y, y]
        if self.C is None or self.gamma is None:
            folds = min(3, int(min(np.sum(y > 0), np.sum(y < 0))))
            if folds < 2:  # too few samples to cross-validate (r = 0 with a one-point POS)
                self.C, self.gamma = 1.0, 1.0
            else:
                search = GridSearchCV(SVC(kernel="rbf"), {"C": GRID, "gamma": GRID}, cv=folds).fit(X, y)
                self.C, self.gamma = search.best_params_["C"], search.best_params_["gamma"]
        self.svm = SVC(kernel="rbf", C=self.C, gamma=self.gamma).fit(X, y)
        self.X, self.y = X[self.svm.support_], y[self.svm.support_]

    def predict_population(self, n, rng, batch=10000, max_draws=50000):
        """n random points in the unit cube that the SVM labels optimal.

        shortcut: when fewer than n of max_draws random points are labelled optimal (a thin positive
        region in many dimensions), the best-scoring rejected points fill the gap; raise max_draws if
        the returned acceptance rate shows this happens often.
        Returns (points, positives_found, draws).
        """
        D = self.svm.support_vectors_.shape[1]
        accepted, best, best_score, draws = [], np.empty((0, D)), np.empty(0), 0
        while draws < max_draws and sum(map(len, accepted)) < n:
            candidates = rng.random((batch, D))
            score = self.svm.decision_function(candidates)
            draws += batch
            accepted.append(candidates[score > 0])
            pool = np.vstack([best, candidates[score <= 0]])
            pool_score = np.r_[best_score, score[score <= 0]]
            top = np.argsort(-pool_score)[:n]
            best, best_score = pool[top], pool_score[top]
        found = sum(map(len, accepted))
        points = np.vstack(accepted)[:n]
        return np.vstack([points, best[:n - len(points)]]), found, draws
