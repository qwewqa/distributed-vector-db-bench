import traceback
import weaviate

from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.terraform import DatabaseDeployment, apply_terraform


class TestWeaviate(Benchmark):
    """A test of the Weaviate database deployment.

    Adds an object and then retrieves it to verify that the database is working correctly.
    """

    def deploy(self):
        return apply_terraform(DatabaseDeployment.WEAVIATE)

    def run(self, config: dict) -> dict:
        client = self.create_weaviate_client(config)

        obj = {
            "name": "vdbbench",
            "content": "Hello, World!",
        }

        class_name = "Document"
        try:
            # Assuming a schema is already created that includes a class "Document"
            uuid = client.data_object.create(data_object=obj, class_name=class_name)

            retrieve_response = client.data_object.get(uuid=uuid, class_name=class_name)
            client.data_object.delete(uuid=uuid, class_name=class_name)

            if retrieve_response["properties"] == obj:
                return {
                    "status": "success",
                    "detail": "Object added and retrieved successfully.",
                }
            else:
                return {
                    "status": "failure",
                    "detail": "Retrieved object does not match the added object.",
                }
        except Exception as e:
            return {
                "status": "failure",
                "detail": f"Weaviate test failed with error: {e}",
                "traceback": f"{traceback.format_exc()}",
            }

    def create_weaviate_client(self, config):
        """Creates a Weaviate client from the configuration.

        Args:
            config: The output from the Terraform module for the Weaviate deployment.

        Returns:
            A Weaviate client.
        """
        return weaviate.Client(
            url=f"http://{config['weaviate_host']}:{config['weaviate_port']}"
        )
