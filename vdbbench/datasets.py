import logging
from pathlib import Path
from typing import Callable, TypeAlias

import h5py
import numpy as np
import requests

from vdbbench.distance import DistanceMetric

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("/tmp/vdbbench/datasets")


DATASETS = {
    "glove-25d": lambda: load_from_hdf5(
        "glove_25d.h5",
        "https://ann-benchmarks.com/glove-25-angular.hdf5",
        DistanceMetric.Angular,
    ),
    "glove-50d": lambda: load_from_hdf5(
        "glove_50d.h5",
        "https://ann-benchmarks.com/glove-50-angular.hdf5",
        DistanceMetric.Angular,
    ),
    "glove-100d": lambda: load_from_hdf5(
        "glove_100d.h5",
        "https://ann-benchmarks.com/glove-100-angular.hdf5",
        DistanceMetric.Angular,
    ),
    "glove-200d": lambda: load_from_hdf5(
        "glove_200d.h5",
        "https://ann-benchmarks.com/glove-200-angular.hdf5",
        DistanceMetric.Angular,
    ),
    "fashion-mnist": lambda: load_from_hdf5(
        "fashion-mnist.h5",
        "https://ann-benchmarks.com/fashion-mnist-784-euclidean.hdf5",
        DistanceMetric.Euclidean,
    ),
}


class Dataset:
    def __init__(
        self,
        metric: DistanceMetric,
        train: np.ndarray,
        test: np.ndarray,
        distances: np.ndarray,
        neighbors: np.ndarray,
    ):
        self.metric = metric
        self.train = train
        self.test = test
        self.distances = distances
        self.neighbors = neighbors

    @property
    def dims(self):
        return self.train.shape[1]


DatasetLoader: TypeAlias = Callable[[], Dataset]


def load_from_hdf5(name: str, url: str, metric: DistanceMetric) -> Dataset:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dl_file = DOWNLOAD_DIR / name
    if dl_file.exists():
        logger.info(f"Using existing dataset file {dl_file}")
    else:
        response = requests.get(url)
        response.raise_for_status()
        with open(dl_file, "wb") as f:
            f.write(response.content)
        logger.info(f"Downloaded dataset file {dl_file}")
    f = h5py.File(dl_file, "r")
    return Dataset(
        metric, f["train"][()], f["test"][()], f["distances"][()], f["neighbors"][()]
    )
