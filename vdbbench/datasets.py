import logging
from pathlib import Path
from typing import Callable

import h5py
import numpy as np
import requests

from vdbbench.distance import DistanceMetric

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("/tmp/vdbbench/datasets")


class Dataset:
    def __init__(
        self,
        train: np.ndarray,
        test: np.ndarray,
        distances: np.ndarray,
        neighbors: np.ndarray,
    ):
        self.train = train
        self.test = test
        self.distances = distances
        self.neighbors = neighbors


class DatasetLoader:
    def __init__(
        self,
        loader: Callable[[], Dataset],
        name: str,
        dims: int,
        metric: DistanceMetric,
    ):
        self.loader = loader
        self.name = name
        self.dims = dims
        self.metric = metric

    def load(self) -> Dataset:
        return self.loader()


def dataset(
    name: str, dims: int, metric: DistanceMetric
) -> Callable[[Callable[[], Dataset]], DatasetLoader]:
    def decorator(loader: Callable[[], Dataset]) -> DatasetLoader:
        return DatasetLoader(loader, name, dims, metric)

    return decorator


def load_from_hdf5(name: str, url: str) -> Dataset:
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
        f["train"][()], f["test"][()], f["distances"][()], f["neighbors"][()]
    )


@dataset("glove_25d", 25, DistanceMetric.Angular)
def glove_25d() -> Dataset:
    return load_from_hdf5(
        "glove_25d.h5", "https://ann-benchmarks.com/glove-25-angular.hdf5"
    )


@dataset("glove_50d", 50, DistanceMetric.Angular)
def glove_50d() -> Dataset:
    return load_from_hdf5(
        "glove_50d.h5", "https://ann-benchmarks.com/glove-50-angular.hdf5"
    )


@dataset("glove_100d", 100, DistanceMetric.Angular)
def glove_100d() -> Dataset:
    return load_from_hdf5(
        "glove_100d.h5", "https://ann-benchmarks.com/glove-100-angular.hdf5"
    )


@dataset("glove_200d", 200, DistanceMetric.Angular)
def glove_200d() -> Dataset:
    return load_from_hdf5(
        "glove_200d.h5", "https://ann-benchmarks.com/glove-200-angular.hdf5"
    )


@dataset("fashion-mnist", 784, DistanceMetric.Euclidean)
def fashion_mnist() -> Dataset:
    return load_from_hdf5(
        "fashion-mnist.h5",
        "https://ann-benchmarks.com/fashion-mnist-784-euclidean.hdf5",
    )
