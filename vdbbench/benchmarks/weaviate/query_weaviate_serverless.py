import numpy as np
import weaviate
import weaviate.classes.config as wc
from weaviate import WeaviateClient

from vdbbench.benchmarks.query_benchmark import QueryBenchmark
from vdbbench.datasets import Dataset
from vdbbench.distance import DistanceMetric
from vdbbench.terraform import DatabaseDeployment, apply_terraform


class QueryWeaviateServerless(QueryBenchmark):
    COLLECTION_NAME = "vdbbench"
    client: WeaviateClient
    collection: weaviate.collections.Collection

    def run_deploy(self) -> dict:
        return apply_terraform(DatabaseDeployment.RUNNER_ONLY)

    def init(self, deploy_output: dict, wcs_url: str, wcs_api_key: str):
        if not wcs_url:
            raise ValueError("wcs_url is required")
        if not wcs_api_key:
            raise ValueError("wcs_api_key is required")

        self.client = weaviate.connect_to_wcs(
            cluster_url=wcs_url,
            auth_credentials=weaviate.auth.AuthApiKey(api_key=wcs_api_key),
        )

    def load_data(self, dataset: Dataset, ef_construction: int = 100, m: int = 16, ef: int = -1):
        self.logger.info("Loading data into Weaviate")
        self.collection = self.client.collections.get(name=self.COLLECTION_NAME)
        return
        client = self.client
        client.collections.delete_all()

        self.collection = client.collections.create(
            name=self.COLLECTION_NAME,
            properties=[
                wc.Property(name="i", data_type=wc.DataType.INT),
            ],
            vectorizer_config=wc.Configure.Vectorizer.none(),
            vector_index_config=wc.Configure.VectorIndex.hnsw(
                ef_construction=ef_construction,
                ef=ef,
                max_connections=m,
                distance_metric={
                    DistanceMetric.Euclidean: wc.VectorDistances.L2_SQUARED,
                    DistanceMetric.Angular: wc.VectorDistances.COSINE,
                }[dataset.metric],
            ),
        )

        with self.collection.batch.dynamic() as batch:
            for i, vector in enumerate(dataset.train):
                batch.add_object(
                    properties={"i": i},
                    vector=vector.tolist(),
                )

        if len(self.collection.batch.failed_objects) > 0:
            raise RuntimeError("Failed to load data")

    def prepare_group(self, ef: int = -1):
        self.collection.config.update(
            vectorizer_config=wc.Reconfigure.VectorIndex.hnsw(ef = ef)
        )

    def prepare_query(self):
        pass

    def query(self, queries: np.ndarray, k: int = 10) -> list[list[int]]:
        if queries.shape[0] > 1:
            raise ValueError("Only one query at a time is supported")
        query = queries[0]
        collection = self.collection
        response = collection.query.near_vector(
            query.tolist(),
            limit=k,
            return_properties=["i"],
        )
        return [[result.properties["i"] for result in response.objects]]
