import logging
import traceback
import weaviate
from time import perf_counter

from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.terraform import DatabaseDeployment, apply_terraform

logger = logging.getLogger(__name__)


class LoadDatasetWeaviate(Benchmark):
    def __init__(
        self,
        dataset,
        config: dict,
        max_vectors: int = -1,
    ):
        self.dataset = dataset
        self.config = config
        self.max_vectors = max_vectors

    def deploy(self) -> dict:
        # This method would implement the deployment of Weaviate using Terraform
        # For simplicity, we're assuming the deployment is already handled outside this class
        return apply_terraform(DatabaseDeployment.WEAVIATE)

    def run(self) -> dict:
        client = weaviate.Client(url=f"http://{self.config['weaviate_host']}:{self.config['weaviate_port']}")

        data = self.dataset.load().train
        if self.max_vectors > 0:
            data = data[:self.max_vectors]

        class_name = "VectorData"
        try:
            # Assuming the schema is already created for simplicity
            start_time = perf_counter()

            logger.info(f"Loading dataset into Weaviate ({len(data)} vectors)")
            for i, vec in enumerate(data):
                obj = {
                    "id": str(i),
                    "vector": vec.tolist(),
                }
                client.data_object.create(data_object=obj, class_name=class_name)

            duration = perf_counter() - start_time

            # Example of querying the first inserted vector
            query_result = client.query.aggregate(class_name=class_name).with_fields('meta {count}').do()
            count = query_result['data']['Aggregate'][class_name]['meta']['count']

            if count == len(data):
                return {
                    "status": "success",
                    "detail": "Dataset loaded and verified successfully.",
                    "duration": duration,
                }
            else:
                return {
                    "status": "failure",
                    "detail": "The number of documents in Weaviate does not match the dataset.",
                }
        except Exception as e:
            logger.error(f"Failed to load dataset into Weaviate: {e}")
            return {
                "status": "failure",
                "detail": f"Test failed with error: {e}",
                "traceback": f"{traceback.format_exc()}",
            }
