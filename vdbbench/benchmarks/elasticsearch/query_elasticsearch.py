from __future__ import annotations

import dataclasses
import itertools
import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Iterable, Literal

import numpy as np
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.benchmarks.elasticsearch.common import (
    create_elasticsearch_client,
    wait_for_elasticsearch_cluster,
)
from vdbbench.datasets import Dataset, DatasetLoader
from vdbbench.distance import DistanceMetric
from vdbbench.terraform import DatabaseDeployment, apply_terraform

logger = logging.getLogger(__name__)


class QueryElasticsearch(Benchmark):
    def __init__(
        self,
        dataset: DatasetLoader,
        node_count: int = 3,
        machine_type: str = "n2-standard-2",
        merge_index: bool = True,
        k: int = 10,
        query_batch_size: int = 100,
        shard_counts: Iterable[int] = (1, 2, 3),
        replica_counts: Iterable[int] = (0, 1, 2),
        ef_construction: Iterable[int] = (100,),
        m: Iterable[int] = (16,),
        num_candidates: Iterable[int] = (10, 20, 40, 80, 160, 320),
    ):
        """Benchmark the latency and recall of a k-NN query on an Elasticsearch cluster.

        Args:
            dataset: The dataset to use for the benchmark.
            node_count: The number of nodes in the Elasticsearch cluster.
            machine_type: The machine type to use for the Elasticsearch nodes.
            merge_index: Whether to merge the index after loading the data.
            k: The number of neighbors to retrieve for each query.
            query_batch_size: The number of queries to run per request.
            shard_counts: The number of shards to use for the index.
            replica_counts: The number of replicas to use for the index.
            ef_construction: The efConstruction parameter for the HNSW index.
            m: The m parameter for the HNSW index.
            num_candidates: The number of candidates to retrieve for each shard the k-NN query.
        """

        self.dataset = dataset
        self.node_count = node_count
        self.machine_type = machine_type
        self.merge_index = merge_index
        self.k = k
        self.query_batch_size = query_batch_size
        self.shard_counts = shard_counts
        self.replica_counts = replica_counts
        self.ef_construction = ef_construction
        self.m = m
        self.num_candidates = num_candidates

    def deploy(self) -> dict:
        return apply_terraform(
            DatabaseDeployment.ELASTICSEARCH,
            node_count=self.node_count,
            machine_type=self.machine_type,
        )

    def run(self, config: dict) -> dict:
        dataset = self.dataset.load()

        for logger_name in ("elasticsearch", "elastic_transport.transport"):
            es_logger = logging.getLogger(logger_name)
            es_logger.setLevel(logging.WARNING)

        logger.info("Waiting for the cluster to be ready")
        es = create_elasticsearch_client(config).options(request_timeout=1000)
        wait_for_elasticsearch_cluster(es)

        result_groups = []
        for shard_count, replica_count, ef_construction, m in itertools.product(
            self.shard_counts,
            self.replica_counts,
            self.ef_construction,
            self.m,
        ):
            data_config = DataConfig(
                shard_count=shard_count,
                replica_count=replica_count,
                ef_construction=ef_construction,
                m=m,
            )
            logger.info(f"Loading data with config: {data_config}")
            load_result = self.load_data(es, dataset.train, data_config)

            query_results = []
            for num_candidates in self.num_candidates:
                query_config = QueryConfig(num_candidates=num_candidates)
                logger.info(f"Running queries with config: {query_config}")
                query_result = self.query(es, dataset, query_config)
                query_results.append(query_result)

            result_groups.append(
                ResultGroup(config=data_config, load=load_result, query=query_results)
            )

        return {
            "options": {
                "dataset": self.dataset.name,
                "node_count": self.node_count,
                "machine_type": self.machine_type,
                "merge_index": self.merge_index,
                "k": self.k,
                "query_batch_size": self.query_batch_size,
                "shard_counts": self.shard_counts,
                "replica_counts": self.replica_counts,
                "ef_construction": self.ef_construction,
                "m": self.m,
                "num_candidates": self.num_candidates,
            },
            "results": [dataclasses.asdict(rg) for rg in result_groups],
        }

    def load_data(
        self, es: Elasticsearch, data: np.ndarray, config: DataConfig
    ) -> LoadResult:
        metric = {
            DistanceMetric.Euclidean: "l2_norm",
            DistanceMetric.Angular: "cosine",
        }[self.dataset.metric]
        name = self.dataset.name

        es.indices.delete(index=name, ignore_unavailable=True)

        start_time = perf_counter()
        logger.info(f"Creating index {name}")
        es.indices.create(
            index=name,
            settings={
                "number_of_shards": config.shard_count,
                "number_of_replicas": config.replica_count,
                "refresh_interval": -1,
            },
            mappings={
                "properties": {
                    "id": {
                        "type": "keyword",
                        "store": "true",
                    },
                    "vec": {
                        "type": "dense_vector",
                        "element_type": "float",
                        "dims": self.dataset.dims,
                        "index": True,
                        "similarity": metric,
                        "index_options": {
                            "type": "hnsw",
                            "ef_construction": config.ef_construction,
                            "m": config.m,
                        },
                    },
                }
            },
        )

        logger.info(f"Loading {len(data)} vectors into the index")

        def chunked():
            for i, vec in enumerate(data):
                if i % (len(data) // 10) == 0:
                    logger.info(f"Loading: {i}/{len(data)}")
                yield {
                    "_index": name,
                    "_id": i,
                    "_source": {
                        "id": i,
                        "vec": vec.tolist(),
                    },
                }

        bulk(
            es,
            chunked(),
            chunk_size=1000,
        )

        if config.replica_count > 0:
            logger.info("Scaling replicas to the desired count")
            es.indices.put_settings(
                index=name,
                body={"index": {"number_of_replicas": config.replica_count}},
            )

        if self.merge_index:
            logger.info("Forcing merge index")
            es.indices.forcemerge(index=name, max_num_segments=1, request_timeout=3000)

        logger.info("Refreshing index")
        es.indices.refresh(index=name)

        logger.info("Waiting for the index status to be green")
        es.cluster.health(wait_for_status="green", index=name)

        return LoadResult(time=perf_counter() - start_time)

    def query(
        self, es: Elasticsearch, dataset: Dataset, config: QueryConfig
    ) -> QueryResult:
        test = dataset.test
        dists = dataset.distances
        n_test = test.shape[0]
        n_batches = test.shape[0] // self.query_batch_size
        k = self.k
        epsilon = 1e-3

        latencies = np.zeros(n_batches)
        recalls = np.zeros(n_test)
        relative_errors = np.zeros(n_test)

        for batch_i in range(n_batches):
            start_i = batch_i * self.query_batch_size
            batch = test[start_i : start_i + self.query_batch_size]

            start_time = perf_counter()
            batch_hits = self.query_batch(es, batch, config)
            latencies[batch_i] = perf_counter() - start_time
            for test_i, hits in enumerate(batch_hits, start=start_i):
                result_vectors = dataset.train[hits]
                true_dist = dists[test_i]
                query = test[test_i]
                result_dist = np.array(
                    [self.dataset.metric(query, v) for v in result_vectors]
                )
                assert (
                    result_dist.shape[0] == k
                ), f"Expected {k} results, got {result_dist.shape}"

                threshold_dist = true_dist[k - 1] + epsilon
                recall = np.sum(result_dist <= threshold_dist) / k
                recalls[test_i] = recall

                true_total_dist = np.sum(true_dist[:k])
                result_total_dist = np.sum(result_dist)
                relative_error = (result_total_dist - true_total_dist) / true_total_dist
                assert (
                    relative_error > -epsilon
                ), f"Relative error is negative: {relative_error}"
                if relative_error < 0:
                    relative_error = 0
                relative_errors[test_i] = relative_error

        return QueryResult(
            config=config,
            recall=Summary.from_array(recalls, worst="min"),
            relative_error=Summary.from_array(relative_errors, worst="max"),
            latency=Summary.from_array(latencies, worst="max"),
        )

    def query_batch(
        self, es: Elasticsearch, queries: np.ndarray, config: QueryConfig
    ) -> list[list[int]]:
        body = []

        for query in queries:
            body.append({})
            body.append(
                {
                    "knn": {
                        "field": "vec",
                        "query_vector": query.tolist(),
                        "k": self.k,
                        "num_candidates": config.num_candidates,
                    },
                    "_source": False,
                    "docvalue_fields": ["id"],
                    "stored_fields": "_none_",
                }
            )

        res = es.msearch(
            index=self.dataset.name,
            body=body,
            filter_path=["responses.hits.hits.fields.id"],
            request_timeout=10,
        )

        return [
            [int(hit["fields"]["id"][0]) for hit in r["hits"]["hits"]]
            for r in res["responses"]
        ]


@dataclass
class ResultGroup:
    config: DataConfig
    load: LoadResult
    query: list[QueryResult]


@dataclass
class DataConfig:
    shard_count: int
    replica_count: int
    ef_construction: int
    m: int


@dataclass
class LoadResult:
    time: float


@dataclass
class QueryConfig:
    num_candidates: int


@dataclass
class QueryResult:
    config: QueryConfig
    recall: Summary
    relative_error: Summary
    latency: Summary


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
