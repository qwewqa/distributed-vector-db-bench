from enum import Enum
from typing import Callable

import numpy as np


class DistanceMetric(Enum):
    def __init__(self, calc: Callable[[np.ndarray, np.ndarray], float]):
        self.calc = calc

    def __call__(self, x: np.ndarray, y: np.ndarray) -> float:
        assert x.shape == y.shape
        assert x.ndim == 1
        return self.calc(x, y)

    Euclidean = (lambda x, y: np.linalg.norm(x - y),)
    Angular = (lambda x, y: 1 - np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y)),)
