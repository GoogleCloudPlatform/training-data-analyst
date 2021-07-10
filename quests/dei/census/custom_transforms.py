from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

class PositionalSelector(BaseEstimator, TransformerMixin):
    def __init__(self, positions):
        self.positions = positions

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return np.array(X)[:, self.positions]


class StripString(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        strip = np.vectorize(str.strip)
        return strip(np.array(X))

class SimpleOneHotEncoder(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        self.values = []
        for c in range(X.shape[1]):
            Y = X[:, c]
            values = {v: i for i, v in enumerate(np.unique(Y))}
            self.values.append(values)
        return self

    def transform(self, X):
        X = np.array(X)
        matrices = []
        for c in range(X.shape[1]):
            Y = X[:, c]
            matrix = np.zeros(shape=(len(Y), len(self.values[c])), dtype=np.int8)
            for i, x in enumerate(Y):
                if x in self.values[c]:
                    matrix[i][self.values[c][x]] = 1
            matrices.append(matrix)
        res = np.concatenate(matrices, axis=1)
        return res