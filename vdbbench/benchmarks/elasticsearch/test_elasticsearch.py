import traceback

from elasticsearch import ConnectionError

from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.benchmarks.elasticsearch.common import (
    create_elasticsearch_client,
    wait_for_elasticsearch_cluster,
)
from vdbbench.terraform import DatabaseDeployment, apply_terraform


class TestElasticsearch(Benchmark):
    """A test of the Elasticsearch database deployment.

    Indexes a document and then retrieves it to verify that the cluster is working correctly.
    """

    def deploy(self):
        return apply_terraform(DatabaseDeployment.ELASTICSEARCH)

    def run(self, deploy_output: dict) -> dict:
        es = create_elasticsearch_client(deploy_output)
        wait_for_elasticsearch_cluster(es)

        doc = {
            "author": "vdbbench",
            "content": "Hello, World!",
        }

        try:
            index_response = es.index(index="test-index", document=doc)
            retrieve_response = es.get(index="test-index", id=index_response["_id"])
            es.indices.delete(index="test-index", ignore=[400, 404])

            if retrieve_response["_source"] == doc:
                return {
                    "status": "success",
                    "detail": "Document indexed and retrieved successfully.",
                }
            else:
                return {
                    "status": "failure",
                    "detail": "Retrieved document does not match the indexed document.",
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
