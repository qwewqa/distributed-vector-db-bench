from __future__ import annotations

import logging
import numpy as np
from weaviate import Client
import weaviate
from vdbbench.benchmarks.query_benchmark import QueryBenchmark
from vdbbench.benchmarks.weaviate.common import (create_weaviate_client)

from vdbbench.datasets import Dataset
from vdbbench.distance import DistanceMetric
from vdbbench.terraform import DatabaseDeployment, apply_terraform

import json

class QueryWeaviate(QueryBenchmark):
    class_name = "vdbbench"
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
        class_name = self.class_name
        data = dataset.train

        self.logger.info(f"Deleting class {class_name} if exists")
        weaviate_client.schema.delete_class(class_name)

        self.logger.info(f"Creating class {class_name}")
        weaviate_client.schema.create_class({
            "class": class_name,
            "vectorIndexType": "hnsw",
            "vectorIndexConfig": {
                "distance": "cosine",
                "ef": -1,
                "efConstruction": 128,
                "vectorCacheMaxObjects": 1000000,
            },
            "properties": [
                {
                    "name": "entity_id",
                    "dataType": ["string"],
                },
                {
                    "name": "vector",
                    "dataType": ["number[]"],  # Corrected data type for vector field
                    "description": "A numerical vector representing the entity",
                    "vectorIndexType": "hnsw",
                    "vectorizePropertyName": False
                },
            ]
        })

        self.logger.info(f"Loading {len(data)} vectors into {class_name}")

        for i, vec in enumerate(data):
            if i % (len(data) // 10) == 0:
                self.logger.info(f"Loading: {i}/{len(data)}")

            # Normalize the vector
            # norm = np.linalg.norm(vec)
            # vec = vec / norm if norm != 0 else vec

            # Ensure vec is a list for JSON serialization
            vector_data = vec.tolist() if isinstance(vec, np.ndarray) else vec

            # self.logger.info("Vector data: " + str(vector_data))

            # Create the data object in Weaviate
            weaviate_client.data_object.create({
                "entity_id": str(i),
            }, vector=vector_data, class_name=class_name)  # Pass class_name as the second argument

            self.logger.info("Data object created, id: " + str(i))

        self.logger.info(f"Data loading completed for {class_name}")

    def prepare_group(self, replica_count: int = 2):
        # Not needed in Weaviate
        pass

    def prepare_query(self):
        # Not needed in Weaviate
        pass

    def query(self, queries: np.ndarray, k: int = 10) -> list[list[int]]:
        results = []
        for query_vec in queries:
            # Start the query and specify the class and properties to retrieve
            result = self.weaviate_client.query.get(
                class_name="vdbbench",
                properties=["entity_id"]
            ).with_near_vector({
                "vector": query_vec,
            }).with_limit(k).do()

            # print(json.dumps(result, indent=2))

            try:
                query_results = result['data']['Get']['Vdbbench']
                entity_ids = [int(obj['entity_id']) for obj in query_results]
                results.append(entity_ids)
            except Exception as e:
                print(f"An error occurred while processing the query results: {str(e)}")

        return results
