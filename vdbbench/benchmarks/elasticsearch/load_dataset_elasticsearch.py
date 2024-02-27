import logging
import traceback
from time import perf_counter

from elasticsearch import ConnectionError
from elasticsearch.helpers import bulk

from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.benchmarks.elasticsearch.common import (
    create_elasticsearch_client,
    wait_for_elasticsearch_cluster,
)
from vdbbench.datasets import DatasetLoader
from vdbbench.terraform import DatabaseDeployment, apply_terraform

logger = logging.getLogger(__name__)


class LoadDatasetElasticsearch(Benchmark):
    def __init__(
        self,
        dataset: DatasetLoader,
        node_count: int = 3,
        shard_count: int = 3,
        replica_count: int = 2,
        max_vectors: int = -1,
    ):
        self.dataset = dataset
        self.node_count = node_count
        self.shard_count = shard_count
        self.replica_count = replica_count
        self.max_vectors = max_vectors

    def deploy(self) -> dict:
        return apply_terraform(
            DatabaseDeployment.ELASTICSEARCH, node_count=self.node_count
        )

    def run(self, config: dict) -> dict:
        data = self.dataset.load().train
        if self.max_vectors > 0:
            data = data[: self.max_vectors]

        logger.info("Waiting for the cluster to be ready")
        es = create_elasticsearch_client(config).options(request_timeout=1000)
        wait_for_elasticsearch_cluster(es)

        try:
            es.indices.delete(index=self.dataset.name, ignore_unavailable=True)

            logger.info(f"Creating index {self.dataset.name}")
            es.indices.create(
                index=self.dataset.name,
                settings={
                    "number_of_shards": self.shard_count,
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
                            "dims": self.dataset.dims,
                            "index": True,
                            "similarity": "l2_norm",
                            "index_options": {
                                "type": "hnsw",
                                "ef_construction": 128,
                                "m": 24,
                            },
                        },
                    }
                },
            )

            start_time = perf_counter()

            logger.info(f"Loading dataset {self.dataset.name} ({len(data)} vectors)")
            bulk(
                es,
                (
                    {
                        "_op_type": "index",
                        "_index": self.dataset.name,
                        "id": str(i),
                        "vec": vec.tolist(),
                    }
                    for i, vec in enumerate(data)
                ),
                chunk_size=10000,
                request_timeout=3000,
            )

            if self.replica_count > 0:
                logger.info("Scaling replicas to the desired count")
                es.indices.put_settings(
                    index=self.dataset.name,
                    body={"index": {"number_of_replicas": self.replica_count}},
                )

            logger.info("Forcing merge index")
            es.indices.forcemerge(index=self.dataset.name, max_num_segments=1)

            logger.info("Refreshing index")
            es.indices.refresh(index=self.dataset.name)

            logger.info("Waiting for the index status to be green")
            es.cluster.health(wait_for_status="green")

            end_time = perf_counter()
            duration = end_time - start_time

            logger.info("Checking index status")
            index_status = es.indices.get(index=self.dataset.name)
            assert (
                int(index_status[self.dataset.name]["settings"]["index"]["number_of_shards"])
                == self.shard_count
            ), "Index has wrong number of shards"
            assert (
                int(index_status[self.dataset.name]["settings"]["index"][
                    "number_of_replicas"
                ])
                == self.replica_count
            ), "Index has wrong number of replicas"
            assert es.count(index=self.dataset.name)["count"] == len(
                data
            ), "Index has wrong number of documents"

            logger.info("Running a test query")
            res = es.search(
                index=self.dataset.name,
                body={
                    "knn": {
                        "field": "vec",
                        "query_vector": data[0].tolist(),
                        "k": 10,
                        "num_candidates": 100,
                    }
                },
                size=10,
                _source=False,
                docvalue_fields=["id"],
                stored_fields="_none_",
                filter_path=["hits.hits.fields.id"],
                request_timeout=90,
            )
            assert (
                len(res["hits"]["hits"]) == 10
            ), "Query returned wrong number of results"
            assert (
                res["hits"]["hits"][0]["fields"]["id"][0] == "0"
            ), "Query returned wrong result"

            logger.info("Deleting index")
            es.indices.delete(index=self.dataset.name)

            return {
                "status": "success",
                "detail": "Dataset loaded successfully.",
                "duration": duration,
            }
        except ConnectionError as e:
            return {
                "status": "failure",
                "detail": f"Elasticsearch connection error: {e}",
                "traceback": f"{traceback.format_exc()}",
            }
        except Exception as e:
            return {
                "status": "failure",
                "detail": f"Test failed with error: {e}",
                "traceback": f"{traceback.format_exc()}",
            }
