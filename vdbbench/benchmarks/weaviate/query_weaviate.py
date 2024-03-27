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
                    "name": "vec",
                    "dataType": ["number[]"],  # Corrected data type for vector field
                },
            ]
        })

        self.logger.info(f"Loading {len(data)} vectors into {class_name}")

        for i, vec in enumerate(data):
            if i % (len(data) // 10) == 0:
                self.logger.info(f"Loading: {i}/{len(data)}")

            # Normalize the vector
            norm = np.linalg.norm(vec)
            vec = vec / norm if norm != 0 else vec

            # Ensure vec is a list for JSON serialization
            vector_data = vec.tolist() if isinstance(vec, np.ndarray) else vec

            # Create the data object in Weaviate
            weaviate_client.data_object.create({
                "entity_id": str(i),
                "vec": vector_data
            }, class_name=class_name)  # Pass class_name as the second argument

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
            # Log the query vector to understand what is being sent
            # Vector - [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 41.0, 89.0, 194.0, 200.0, 141.0, 97.0, 106.0, 114.0, 133.0, 208.0, 201.0, 69.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 221.0, 245.0, 228.0, 230.0, 246.0, 243.0, 227.0, 215.0, 240.0, 246.0, 240.0, 214.0, 235.0, 188.0, 22.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 169.0, 211.0, 189.0, 179.0, 191.0, 219.0, 241.0, 246.0, 247.0, 245.0, 232.0, 202.0, 186.0, 184.0, 207.0, 220.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 16.0, 202.0, 189.0, 194.0, 195.0, 190.0, 189.0, 194.0, 208.0, 212.0, 199.0, 186.0, 185.0, 194.0, 190.0, 185.0, 203.0, 75.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 81.0, 211.0, 191.0, 191.0, 191.0, 190.0, 190.0, 187.0, 188.0, 188.0, 187.0, 189.0, 192.0, 193.0, 195.0, 191.0, 199.0, 156.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 130.0, 207.0, 191.0, 193.0, 193.0, 189.0, 190.0, 191.0, 192.0, 190.0, 186.0, 189.0, 190.0, 192.0, 195.0, 191.0, 197.0, 200.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 153.0, 203.0, 186.0, 194.0, 192.0, 189.0, 190.0, 190.0, 192.0, 192.0, 189.0, 186.0, 186.0, 187.0, 195.0, 190.0, 192.0, 231.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 184.0, 202.0, 194.0, 206.0, 190.0, 191.0, 194.0, 195.0, 195.0, 197.0, 199.0, 196.0, 193.0, 192.0, 198.0, 196.0, 187.0, 202.0, 41.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 205.0, 200.0, 196.0, 247.0, 205.0, 193.0, 197.0, 197.0, 197.0, 197.0, 198.0, 198.0, 200.0, 186.0, 222.0, 228.0, 189.0, 206.0, 89.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 224.0, 197.0, 214.0, 254.0, 192.0, 193.0, 197.0, 197.0, 197.0, 197.0, 197.0, 197.0, 197.0, 181.0, 233.0, 249.0, 192.0, 207.0, 137.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 11.0, 230.0, 198.0, 236.0, 254.0, 185.0, 195.0, 198.0, 198.0, 199.0, 198.0, 198.0, 199.0, 195.0, 192.0, 201.0, 249.0, 200.0, 203.0, 175.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 47.0, 230.0, 204.0, 243.0, 242.0, 187.0, 196.0, 198.0, 199.0, 199.0, 199.0, 199.0, 200.0, 195.0, 200.0, 187.0, 204.0, 232.0, 200.0, 213.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 84.0, 232.0, 210.0, 242.0, 217.0, 192.0, 196.0, 199.0, 200.0, 200.0, 199.0, 199.0, 200.0, 198.0, 202.0, 184.0, 119.0, 255.0, 200.0, 230.0, 7.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 106.0, 232.0, 224.0, 216.0, 167.0, 208.0, 190.0, 200.0, 200.0, 200.0, 200.0, 199.0, 198.0, 199.0, 195.0, 209.0, 80.0, 255.0, 204.0, 230.0, 59.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 129.0, 223.0, 239.0, 195.0, 121.0, 220.0, 190.0, 199.0, 200.0, 200.0, 202.0, 199.0, 196.0, 200.0, 189.0, 222.0, 67.0, 248.0, 215.0, 230.0, 89.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 149.0, 219.0, 244.0, 190.0, 103.0, 226.0, 190.0, 200.0, 200.0, 201.0, 200.0, 201.0, 199.0, 199.0, 192.0, 227.0, 90.0, 229.0, 222.0, 225.0, 108.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 157.0, 215.0, 244.0, 169.0, 111.0, 228.0, 192.0, 200.0, 201.0, 201.0, 200.0, 202.0, 200.0, 200.0, 193.0, 232.0, 39.0, 209.0, 229.0, 220.0, 112.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 160.0, 214.0, 246.0, 130.0, 137.0, 225.0, 195.0, 200.0, 201.0, 202.0, 201.0, 203.0, 202.0, 198.0, 186.0, 233.0, 80.0, 194.0, 244.0, 223.0, 116.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 163.0, 212.0, 248.0, 103.0, 163.0, 217.0, 198.0, 201.0, 202.0, 201.0, 200.0, 203.0, 201.0, 200.0, 193.0, 222.0, 132.0, 158.0, 246.0, 218.0, 123.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 169.0, 208.0, 250.0, 100.0, 183.0, 214.0, 201.0, 204.0, 205.0, 205.0, 203.0, 206.0, 204.0, 204.0, 197.0, 220.0, 141.0, 115.0, 250.0, 214.0, 135.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 167.0, 213.0, 247.0, 88.0, 194.0, 205.0, 194.0, 195.0, 196.0, 197.0, 198.0, 199.0, 199.0, 196.0, 190.0, 208.0, 170.0, 93.0, 251.0, 213.0, 139.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 164.0, 214.0, 247.0, 64.0, 215.0, 226.0, 212.0, 213.0, 214.0, 214.0, 214.0, 216.0, 214.0, 213.0, 211.0, 230.0, 197.0, 43.0, 252.0, 215.0, 146.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 155.0, 221.0, 243.0, 26.0, 253.0, 229.0, 227.0, 228.0, 228.0, 228.0, 229.0, 229.0, 229.0, 229.0, 226.0, 237.0, 226.0, 2.0, 252.0, 222.0, 146.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 152.0, 210.0, 243.0, 36.0, 252.0, 255.0, 215.0, 215.0, 215.0, 214.0, 248.0, 250.0, 211.0, 211.0, 208.0, 255.0, 232.0, 0.0, 243.0, 217.0, 150.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 146.0, 222.0, 220.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 245.0, 215.0, 151.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 160.0, 242.0, 209.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 213.0, 235.0, 179.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 176.0, 250.0, 217.0, 0.0, 0.0, 3.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 0.0, 0.0, 228.0, 255.0, 199.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 40.0, 47.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 90.0, 142.0, 58.0, 0.0, 0.0, 0.0]

            norm = np.linalg.norm(query_vec)
            query_vec = query_vec / norm if norm != 0 else query_vec
            print(f"Vector - {query_vec.tolist()}")

            # Start the query and specify the class and properties to retrieve
            query_builder = self.weaviate_client.query.get(
                class_name=self.class_name,
                properties=["entity_id", "vec"]
            )

            # Add the vector search conditions using with_near_vector
            query_builder = query_builder.with_near_vector({
                "vector": query_vec.tolist(),
                "limit": k  # 'limit' determines how many nearest neighbors to return
            })

            # Execute the query
            result = query_builder.do()
            print(result)

            # Process the results
            if 'data' in result and 'Get' in result['data'] and self.class_name in result['data']['Get']:
                query_results = result['data']['Get'][self.class_name]
                results.append([int(obj['id']) for obj in query_results])

        return results
