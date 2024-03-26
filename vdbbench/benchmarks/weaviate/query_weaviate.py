from __future__ import annotations

import logging
import numpy as np
from weaviate import Client
from vdbbench.benchmarks.query_benchmark import QueryBenchmark
from vdbbench.benchmarks.weaviate.common import (create_weaviate_client)

from vdbbench.datasets import Dataset
from vdbbench.distance import DistanceMetric
from vdbbench.terraform import DatabaseDeployment, apply_terraform


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
        self.weaviate_client = create_weaviate_client(deploy_output)

    def load_data(
            self,
            dataset: Dataset,
            merge_index: bool = True,
            shard_count: int = 3,
            ef_construction: int = 100,
            m: int = 16,
    ) -> dict:
        weaviate_client = self.weaviate_client
        class_name = self.INDEX_NAME
        data = dataset.train
        metric = {
            DistanceMetric.Euclidean: "cosine",
            DistanceMetric.Angular: "cosine",
        }[dataset.metric]

        self.logger.info(f"Deleting class {class_name} if exists")
        weaviate_client.schema.delete_class(class_name, force=True)

        self.logger.info(f"Creating class {class_name}")
        weaviate_client.schema.create_class({
            "class": class_name,
            "properties": [
                {
                    "name": "id",
                    "dataType": ["int"],
                    "index": True
                },
                {
                    "name": "vec",
                    "dataType": ["vector"],
                    "vectorIndexType": "hnsw",
                    "index": True,
                    "dimension": dataset.dims,
                    "metricType": metric,
                },
            ]
        })

        self.logger.info(f"Loading {len(data)} vectors into {class_name}")

        for i, vec in enumerate(data):
            if i % (len(data) // 10) == 0:
                self.logger.info(f"Loading: {i}/{len(data)}")

            weaviate_client.data_object.create({
                "id": i,
                "vec": vec,
            }, class_name=class_name)


        self.logger.info(f"Data loading completed for {class_name}")