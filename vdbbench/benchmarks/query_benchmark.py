from __future__ import annotations

import dataclasses
import inspect
import itertools
import json
import logging
from abc import abstractmethod
from dataclasses import dataclass
from time import perf_counter
from typing import Literal

import numpy as np

from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.datasets import DATASETS, Dataset


class QueryBenchmark(Benchmark):
    """A benchmark that runs queries on a database.

    This class is designed to be subclassed to implement a specific database benchmark
    by implementing the abstract methods.

    Configuration is in the following format: {
        "deploy": {
            // run_deploy arguments
        },
        "data": {
            "dataset": <dataset name>,
            // load_data arguments
        },
        "group": {
            // prepare_group arguments
        },
        "query": {
            "rounds": <number of rounds to run for each query configuration>,
            "k": <number of nearest neighbors to return for each query>,
            "batch_size": <number of queries to run in each batch>,
            // query and prepare_query arguments
        },
    }
    "data", "group", and "query" support starred keys, allowing all combinations of the values to be tested.
    For example, the query configuration {"*batch_size": [100, 200], "*k": [10, 20]} will result in the following configurations:
    {"batch_size": 100, "k": 10}, {"batch_size": 100, "k": 20}, {"batch_size": 200, "k": 10}, {"batch_size": 200, "k": 20}.

    load_data is called once for each data configuration.
    For each data configuration, prepare_group is called once for each group configuration.
    For each group configuration, prepare_query and query are called once for each round of queries for each query configuration.
    For example given data configurations d1 and d2, group configurations g1 and g2, and query configurations q1 and q2, the following calls are made:
        prepare_group(g1)
            repeat for q1["rounds"]: prepare_query(q1) query(q1)
            repeat for q2["rounds"]: prepare_query(q2) query(q2)
        prepare_group(g2)
            repeat for q1["rounds"]: prepare_query(q1) query(q1)
            repeat for q2["rounds"]: prepare_query(q2) query(q2)
    load_data(d2)
        prepare_group(g1)
            repeat for q1["rounds"]: prepare_query(q1) query(q1)
            repeat for q2["rounds"]: prepare_query(q2) query(q2)
        prepare_group(g2)
            repeat for q1["rounds"]: prepare_query(q1) query(q1)
            repeat for q2["rounds"]: prepare_query(q2) query(q2)
    """

    def __init__(
        self,
        deploy: dict | None = None,
        data: dict | None = None,
        group: dict | None = None,
        query: dict | None = None,
    ):
        self.deploy_config = deploy or {}
        self.data_config = data or {}
        self.group_config = group or {}
        self.query_config = query or {}
        self.logger = logging.getLogger(f"{__name__}.{type(self).__name__}")

    @abstractmethod
    def run_deploy(self, **kwargs) -> dict:
        """Deploys the the resources for the benchmark."""

    @abstractmethod
    def init(self, deploy_output: dict):
        """Initializes the benchmark.

        This method is called once before the benchmark is run.
        It can be used to perform any setup that should not be included in the benchmark time,
        like opening a connection to the database and waiting for it to be ready.
        """

    @abstractmethod
    def load_data(self, dataset: Dataset, **kwargs):
        """Loads the data into the database.

        This method should clear the database and load the train data from the given numpy array.
        """

    @abstractmethod
    def prepare_group(self, **kwargs):
        """Does preparation at the start of a group.

        This method is called once for each group of queries.
        It can be used to make modifications to the database which don't require the data to be reloaded entirely.
        """

    @abstractmethod
    def prepare_query(self, **kwargs):
        """Does preparation at the start of a round of queries.

        This method is called once for each round of queries.
        It can be used to clear caches or perform other operations that should not be included in the query time.
        """

    @abstractmethod
    def query(self, queries: np.ndarray, k: int, **kwargs) -> list[list[int]]:
        """Runs a batch of queries.

        Args:
            queries: The queries to run, as a numpy array with each row being a query.
            k: The number of nearest neighbors to return for each query.
            **kwargs: Additional keyword arguments for the query.

        Returns:
            A list of lists of integers. Each row contains the train indices of the k nearest neighbors for
            the corresponding row in the query.
        """

    def deploy(self) -> dict:
        self.validate_config()
        return self._call_with_config(self.run_deploy, self.deploy_config)

    def run(self, deploy_output: dict) -> dict:
        self._backfill_config(self.deploy_config, self.run_deploy)
        self._backfill_config(self.data_config, self.load_data)
        self._backfill_config(self.group_config, self.prepare_group)
        self._backfill_config(self.query_config, self.prepare_query)
        self._backfill_config(self.query_config, self.query)

        data_configs = self._produce_combinations(self.data_config)
        group_configs = self._produce_combinations(self.group_config)
        query_configs = self._produce_combinations(self.query_config)
        self.logger.info(f"{len(data_configs)} data configuration(s)")
        self.logger.info(f"{len(group_configs)} group configuration(s)")
        self.logger.info(f"{len(query_configs)} query configuration(s)")
        self.logger.info(
            f"{len(data_configs) * len(group_configs) * len(query_configs)} total configuration(s)"
        )

        self.init(deploy_output)
        results = []
        for data_config in data_configs:
            self.logger.info(f"Running data configuration: {data_config}")
            dataset_name = data_config["dataset"]
            dataset = self._load_dataset(dataset_name)
            self._call_with_config(self.load_data, (data_config | {"dataset": dataset}))
            group_results = []
            for group_config in group_configs:
                self.logger.info(f"Running group configuration: {group_config}")
                self._call_with_config(self.prepare_group, group_config)
                query_results = []
                for query_config in query_configs:
                    self.logger.info(f"Running query configuration: {query_config}")
                    query_result = self._do_queries(dataset, query_config)
                    query_results.append(query_result)
                    self.logger.info(f"Query result: {query_result}")
                group_results.append(
                    GroupResult(group_config=group_config, queries=query_results)
                )
            results.append(DataResult(data_config=data_config, groups=group_results))
        return dataclasses.asdict(
            QueryBenchmarkResult(deploy_config=self.deploy_config, data=results)
        )

    def _load_dataset(self, dataset: str) -> Dataset:
        self.logger.info(f"Loading dataset {dataset}")
        return DATASETS[dataset]()

    def _do_queries(self, dataset: Dataset, query_config: dict) -> QueryResult:
        rounds = query_config.setdefault("rounds", 1)
        if rounds < 1:
            raise ValueError("Expected at least 1 round")
        results = []
        for i in range(rounds):
            self.logger.info(f"Running query round {i + 1}/{rounds}")
            results.append(self._do_query_round(dataset, query_config))
        latency = np.concatenate([r.latency for r in results])
        recall = np.concatenate([r.recall for r in results])
        relative_error = np.concatenate([r.relative_error for r in results])
        return QueryResult(
            query_config=query_config,
            latency=Summary.from_array(latency, worst="max"),
            recall=Summary.from_array(recall, worst="min"),
            relative_error=Summary.from_array(relative_error, worst="max"),
        )

    def _do_query_round(self, dataset: Dataset, query_config: dict) -> QueryRoundResult:
        epsilon = 1e-3
        batch_size = query_config.setdefault("batch_size", 100)
        k = query_config.setdefault(
            "k", self._get_default_args(self.query).get("k", 10)
        )
        train = dataset.train
        test = dataset.test
        dists = dataset.distances
        n_test = test.shape[0]
        n_batches = n_test // batch_size

        self.logger.info("Preparing for queries")
        self._call_with_config(self.prepare_query, query_config)

        self.logger.info(
            f"Running {n_test} queries in {n_batches} batches of {batch_size}"
        )
        latency = np.zeros(n_batches)
        recall = np.zeros(n_test)
        relative_error = np.zeros(n_test)
        for batch_i in range(n_batches):
            start = batch_i * batch_size
            end = (batch_i + 1) * batch_size
            queries = test[start:end]
            start_time = perf_counter()
            response = self._call_with_config(self.query, query_config, queries=queries)
            latency[batch_i] = perf_counter() - start_time
            assert (
                len(response) == queries.shape[0]
            ), f"Expected {queries.shape[0]} responses, got {len(response)}"
            assert (
                len(response[0]) == k
            ), f"Expected {k} neighbors, got {len(response[0])}"
            for i, neighbor_ids in enumerate(response, start=start):
                result_vectors = train[neighbor_ids]
                true_dists = dists[i]
                query_vector = test[i]
                result_dists = np.array(
                    [
                        dataset.metric(query_vector, result_vector)
                        for result_vector in result_vectors
                    ]
                )
                recall[i] = self._calc_recall(k, true_dists, result_dists, epsilon)
                relative_error[i] = self._calc_relative_error(
                    k, true_dists, result_dists, epsilon
                )

        return QueryRoundResult(
            latency=latency,
            recall=recall,
            relative_error=relative_error,
        )

    def _calc_recall(
        self, k: int, true_dists: np.ndarray, result_dists: np.ndarray, epsilon: float
    ) -> float:
        threshold_dist = true_dists[k - 1] * (1 + epsilon)
        return np.sum(result_dists <= threshold_dist) / k

    def _calc_relative_error(
        self, k: int, true_dists: np.ndarray, result_dists: np.ndarray, epsilon: float
    ) -> float:
        true_total_dist = np.sum(true_dists[:k])
        result_total_dist = np.sum(result_dists)
        relative_error = (result_total_dist - true_total_dist) / true_total_dist
        assert (
            relative_error >= -epsilon
        ), f"Relative error is negative: {relative_error}"
        if relative_error < 0:
            return 0
        return relative_error

    @staticmethod
    def _produce_combinations(config: dict) -> list[dict]:
        """Produces all combinations of a configuration dictionary.

        The cartesian product of the values of each key with a star (*) prefix is taken, and the resulting
        dictionaries are returned in a list.

        Args:
            config: The configuration dictionary.

        Returns:
            A list of dictionaries, each containing a different combination of the configuration values.

        Raises:
            ValueError: If a starred key does not have a list as its value.

        Example:
            _produce_combinations({"a": [1, 2], "*b": [3, 4]})
            # [{"a": 1, "b": 3}, {"a": 1, "b": 4}, {"a": 2, "b": 3}, {"a": 2, "b": 4}]
        """
        new_config = {}
        for k, v in config.items():
            if k.startswith("*"):
                k = k[1:]
                if not isinstance(v, list):
                    raise ValueError(f"Expected list for starred key {k}")
                new_config[k] = v
            else:
                new_config[k] = [v]
        return [
            dict(zip(new_config.keys(), combination))
            for combination in itertools.product(*new_config.values())
        ]

    def validate_config(self):
        if any(k.startswith("*") for k in self.deploy_config.keys()):
            raise ValueError("Starred keys are not allowed in deploy configuration")
        self._validate_config_has_required_keys(
            self.deploy_config, self._get_required_arg_names(self.run_deploy), "deploy"
        )
        self._validate_all_config_values_used(
            self.deploy_config, self._get_arg_names(self.run_deploy), "deploy"
        )

        self._validate_config_has_required_keys(
            self.data_config, self._get_required_arg_names(self.load_data), "data"
        )
        self._validate_all_config_values_used(
            self.data_config, self._get_arg_names(self.load_data), "data"
        )

        self._validate_config_has_required_keys(
            self.group_config, self._get_required_arg_names(self.prepare_group), "group"
        )
        self._validate_all_config_values_used(
            self.group_config, self._get_arg_names(self.prepare_group), "group"
        )

        self._validate_config_has_required_keys(
            self.query_config,
            (
                self._get_required_arg_names(self.query)
                | self._get_required_arg_names(self.prepare_query)
            )
            - {"queries", "k"},
            "query",
        )
        self._validate_all_config_values_used(
            self.query_config,
            {"batch_size", "rounds"}
            | self._get_arg_names(self.query)
            | self._get_arg_names(self.prepare_query),
            "query",
        )

    @classmethod
    def _call_with_config(cls, f, config: dict, **kwargs):
        cls._backfill_config(config, f)
        return f(
            **{
                k: v
                for k, v in config.items()
                if k in cls._get_arg_names(f) and k not in kwargs
            },
            **kwargs,
        )

    @classmethod
    def _backfill_config(cls, config: dict, f):
        for k, v in cls._get_default_args(f).items():
            if (
                k not in config
                and f"*{k}" not in config
                and cls._is_json_serializable(v)
            ):
                config[k] = v
        return config

    @staticmethod
    def _is_json_serializable(value) -> bool:
        try:
            if dataclasses.is_dataclass(value):
                value = dataclasses.asdict(value)
            json.dumps(value)
            return True
        except TypeError:
            return False

    @staticmethod
    def _get_default_args(f) -> dict:
        return {
            k: v.default
            for k, v in inspect.signature(f).parameters.items()
            if v.default is not inspect.Parameter.empty
        }

    @staticmethod
    def _get_arg_names(f) -> set[str]:
        return set(inspect.signature(f).parameters.keys())

    @staticmethod
    def _get_required_arg_names(f) -> set[str]:
        return {
            k
            for k, v in inspect.signature(f).parameters.items()
            if v.default is inspect.Parameter.empty
        }

    @staticmethod
    def _validate_config_has_required_keys(
        config: dict, required: set[str], prefix: str
    ):
        missing = required - set(config.keys())
        if missing:
            raise ValueError(
                f"Missing required configuration values: {prefix}.({', '.join(missing)})"
            )

    @staticmethod
    def _validate_all_config_values_used(config: dict, used: set[str], prefix: str):
        unused = set(k[1:] if k.startswith("*") else k for k in config.keys()) - used
        if unused:
            raise ValueError(
                f"Unused configuration values: {prefix}.({', '.join(unused)})"
            )


@dataclass
class QueryBenchmarkResult:
    deploy_config: dict
    data: list[DataResult]


@dataclass
class DataResult:
    data_config: dict
    groups: list[GroupResult]


@dataclass
class GroupResult:
    group_config: dict
    queries: list[QueryResult]


@dataclass
class QueryResult:
    query_config: dict
    latency: Summary
    recall: Summary
    relative_error: Summary


@dataclass
class QueryRoundResult:
    latency: np.ndarray
    recall: np.ndarray
    relative_error: np.ndarray


@dataclass
class Summary:
    mean: float
    std: float
    min: float
    max: float
    p25: float
    p50: float
    p75: float
    p90: float
    p95: float
    p99: float
    p999: float

    @classmethod
    def from_array(cls, arr: np.ndarray, worst: Literal["max", "min"]) -> Summary:
        def percentile(p):
            return np.percentile(arr, p if worst == "max" else 100 - p)

        return cls(
            mean=arr.mean(),
            std=arr.std(),
            min=arr.min(),
            max=arr.max(),
            p25=percentile(25),
            p50=percentile(50),
            p75=percentile(75),
            p90=percentile(90),
            p95=percentile(95),
            p99=percentile(99),
            p999=percentile(99.9),
        )
