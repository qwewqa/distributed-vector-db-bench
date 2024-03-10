import traceback
from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.terraform import DatabaseDeployment, apply_terraform
from vdbbench.benchmarks.tigergraph.common import create_tigergraph_client, wait_for_tigergraph_cluster
from vdbbench.benchmarks.tigergraph.common import create_schema, add_vertex, add_edge, run_query


class TestTigerGraph(Benchmark):
    """A test of the TigerGraph database deployment.

    Creates a simple graph schema, inserts vertices and edges, then retrieves them to verify the graph database is working correctly.
    """

    import requests
    import json
    def deploy(self):
        return apply_terraform(DatabaseDeployment.TIGERGRAPH)

    def run(self, config: dict) -> dict:
        tg = create_tigergraph_client(config)
        wait_for_tigergraph_cluster(tg)

        try:
            create_schema(tg)
            add_vertex(tg, "Person", "1", {"name": "John Doe"})
            add_edge(tg, "Knows", "1", "2")

            query_result = run_query(tg, "example_query", parameters={"person_id": "1"})

            # Validate query results (simplified example)
            if query_result and "name" in query_result[0]:
                return {
                    "status": "success",
                    "detail": "Graph schema created, vertex inserted, and query executed successfully.",
                }
            else:
                return {
                    "status": "failure",
                    "detail": "Query did not return the expected results.",
                }
        except Exception as e:
            return {
                "status": "failure",
                "detail": f"Test failed with error: {e}",
                "traceback": f"{traceback.format_exc()}",
            }
