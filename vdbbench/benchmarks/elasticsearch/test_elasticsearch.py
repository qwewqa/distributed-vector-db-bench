from elasticsearch import Elasticsearch, ConnectionError
from vdbbench.benchmarks.benchmark import Benchmark

from vdbbench.terraform import DatabaseDeployment, apply_terraform


class TestElasticsearch(Benchmark):
    def deploy(self):
        return apply_terraform(DatabaseDeployment.ELASTICSEARCH)

    def run(self, config: dict) -> dict:
        instance_hosts = config["elasticsearch_instance_names"]

        es_hosts = [{"host": host, "port": 9200, "scheme": "http"} for host in instance_hosts]
        es = Elasticsearch(hosts=es_hosts)

        doc = {
            "author": "vdbbench",
            "content": "Hello, World!",
        }

        try:
            index_response = es.index(index="test-index", document=doc)
            retrieve_response = es.get(index="test-index", id=index_response["_id"])

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
                "detail": f"Elasticsearch connection error: {str(e)}",
            }
        except Exception as e:
            return {"status": "failure", "detail": f"Test failed with error: {str(e)}"}
