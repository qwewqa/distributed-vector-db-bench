from __future__ import annotations

import logging
import numpy as np
from weaviate import Client
from vdbbench.benchmarks.query_benchmark import QueryBenchmark
from vdbbench.datasets import Dataset
from vdbbench.terraform import apply_terraform, DatabaseDeployment


class QueryWeaviate(QueryBenchmark):
    CLASS_NAME = "vdbbench"
    weaviate_client: Client

    def run_deploy(
        self, node_count: int = 3, machine_type: str = "n2-standard-2"
    ) -> dict:
        # Deployment logic for Weaviate (assuming the use of Terraform)
        return apply_terraform(
            DatabaseDeployment.WEAVIATE,
            node_count=node_count,
            machine_type=machine_type,
        )

    def init(self, deploy_output: dict):
        self.logger.info("Initializing Weaviate client")
        # Initialize the Weaviate client (endpoint and authentication details needed)
        self.weaviate_client = Client("http://weaviate-instance:8080")

    def load_data(
        self,
        dataset: Dataset,
        merge_index: bool = True,
        shard_count: int = 3,
        ef_construction: int = 100,
        m: int = 16,
    ) -> dict:
        # Logic to load data into Weaviate
        pass

    def prepare_group(self, replica_count: int = 2):
        # This function may not be necessary for Weaviate
        pass

    def prepare_query(self):
        # Prepare for the query execution, like clearing cache
        pass

    def query(
        self, queries: np.ndarray, k: int = 10, num_candidates: int = 160
    ) -> list[list[int]]:
        # Query execution logic using Weaviate
        pass
