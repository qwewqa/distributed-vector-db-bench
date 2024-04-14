from __future__ import annotations

import logging

import numpy as np
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from vdbbench.benchmarks.elasticsearch.common import (
    create_elasticsearch_client,
    wait_for_elasticsearch_cluster,
)
from vdbbench.benchmarks.query_benchmark import QueryBenchmark
from vdbbench.datasets import Dataset
from vdbbench.distance import DistanceMetric
from vdbbench.terraform import DatabaseDeployment, apply_terraform


class QueryElasticsearch(QueryBenchmark):
    INDEX_NAME = "vdbbench"
    es: Elasticsearch

    def run_deploy(
        self, node_count: int = 3, machine_type: str = "n2-standard-2"
    ) -> dict:
        return apply_terraform(
            DatabaseDeployment.ELASTICSEARCH,
            node_count=node_count,
            machine_type=machine_type,
        )

    def init(self, deploy_output: dict):
        for logger_name in ("elasticsearch", "elastic_transport.transport"):
            logging.getLogger(logger_name).setLevel(logging.WARNING)

        self.logger.info("Waiting for the cluster to be ready")
        es = create_elasticsearch_client(deploy_output).options(request_timeout=1000)
        wait_for_elasticsearch_cluster(es)
        self.es = es

    def load_data(
        self,
        dataset: Dataset,
        shard_count: int = 3,
        ef_construction: int = 100,
        m: int = 16,
    ) -> dict:
        es = self.es
        name = self.INDEX_NAME
        data = dataset.train
        metric = {
            DistanceMetric.Euclidean: "l2_norm",
            DistanceMetric.Angular: "cosine",
        }[dataset.metric]

        es.indices.delete(index=name, ignore_unavailable=True)

        self.logger.info(f"Creating index {name}")
        es.indices.create(
            index=name,
            settings={
                "number_of_shards": shard_count,
                "number_of_replicas": 0,
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
                        "dims": dataset.dims,
                        "index": True,
                        "similarity": metric,
                        "index_options": {
                            "type": "hnsw",
                            "ef_construction": ef_construction,
                            "m": m,
                        },
                    },
                }
            },
        )

        self.logger.info(f"Loading {len(data)} vectors into the index")

        def chunked():
            for i, vec in enumerate(data):
                if i % (len(data) // 10 + 1) == 0:
                    self.logger.info(f"Loading: {i}/{len(data)}")
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

        self.logger.info("Refreshing index")
        es.indices.refresh(index=name)

        self.logger.info("Waiting for the index status to be green")
        es.cluster.health(wait_for_status="green", index=name)

    def prepare_group(self, replica_count: int = 2):
        if replica_count > 0:
            self.logger.info("Scaling replicas to the desired count")
            self.es.indices.put_settings(
                index=self.INDEX_NAME,
                body={"index": {"number_of_replicas": replica_count}},
            )

    def prepare_query(self):
        self.logger.info("Clearing cache")
        self.es.indices.clear_cache(index=self.INDEX_NAME)
        self.logger.info("Forcing merge index")
        self.es.indices.forcemerge(index=self.INDEX_NAME, max_num_segments=1, request_timeout=3000)

    def query(
        self, queries: np.ndarray, k: int = 10, num_candidates: int = 160
    ) -> list[list[int]]:
        body = []

        for query in queries:
            body.append({})
            body.append(
                {
                    "knn": {
                        "field": "vec",
                        "query_vector": query.tolist(),
                        "k": k,
                        "num_candidates": num_candidates,
                    },
                    "size": k,
                    "_source": False,
                    "docvalue_fields": ["id"],
                    "stored_fields": "_none_",
                }
            )

        res = self.es.msearch(
            index=self.INDEX_NAME,
            body=body,
            filter_path=["responses.hits.hits.fields.id"],
            request_timeout=100,
        )

        return [
            [int(hit["fields"]["id"][0]) for hit in r["hits"]["hits"]]
            for r in res["responses"]
        ]
