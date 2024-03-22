
import logging
import traceback
import weaviate
from time import perf_counter

from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.terraform import DatabaseDeployment, apply_terraform

logger = logging.getLogger(__name__)

import logging
import traceback
from time import perf_counter

from weaviate.client import Client
from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.datasets import DatasetLoader
from vdbbench.terraform import DatabaseDeployment, apply_terraform

logger = logging.getLogger(__name__)


class LoadDatasetWeaviate(Benchmark):
    def __init__(
        self,
        dataset: DatasetLoader,
        node_count: int = 1,

    ):
        self.dataset = dataset
        self.node_count = node_count

    def deploy(self) -> dict:
        return apply_terraform(
            DatabaseDeployment.WEAVIATE, node_count=self.node_count
        )

    def run(self, config: dict) -> dict:
        data = self.dataset.load().train

        logger.info("Connecting to Weaviate cluster")
        client = Client(url=config['url'])

        try:
            logger.info(f"Creating class in Weaviate for dataset {self.dataset.name}")
            client.schema.create_class({
                "class": self.dataset.name,
                "properties": [
                    {"name": "id", "dataType": ["string"]},
                    {"name": "vec", "dataType": ["number"], "vectorize": True}
                ],
                "vectorIndexType": "hnsw",
                "vectorIndexConfig": {
                    "efConstruction": 128,
                    "maxConnections": 16
                }
            })

            start_time = perf_counter()

            logger.info(f"Loading dataset {self.dataset.name} ({len(data)} vectors)")
            for i, vec in enumerate(data):
                client.data_object.create(
                    data_object={"id": str(i), "vec": vec.tolist()},
                    class_name=self.dataset.name
                )

            end_time = perf_counter()
            duration = end_time - start_time

            logger.info("Running a test query")
            res = client.query.get(
                class_name=self.dataset.name,
                properties=["id"],
                where={
                    "path": ["vec"],
                    "operator": "NearVector",
                    "valueVector": data[0].tolist(),
                    "certainty": 0.8
                },
                limit=10
            )

            assert len(res['data']['Get'][self.dataset.name]) == 10, "Query returned wrong number of results"

            logger.info("Deleting class in Weaviate")
            client.schema.delete_class(self.dataset.name)

            return {
                "status": "success",
                "detail": "Dataset loaded successfully.",
                "duration": duration,
            }
        except Exception as e:
            return {
                "status": "failure",
                "detail": f"Test failed with error: {e}",
                "traceback": f"{traceback.format_exc()}",
            }