import time

from elasticsearch import ConnectionError, Elasticsearch
from neo4j.exceptions import Neo4jError
from neo4j import GraphDatabase, Driver


def create_neo4j_client(
        config: dict,
) -> Driver:
    """Creates a Neo4j client from the configuration.

    Args:
        config: The output from the Terraform module for the Neo4j deployment.

    Returns:
        An Neo4j client.
    """
    # URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
    URI = "<URI for Neo4j database>"
    AUTH = ("<Username>", "<Password>")

    driver = GraphDatabase.driver(URI, auth=AUTH)
    driver.verify_connectivity()
    return driver


def wait_for_elasticsearch_cluster(
        es: Elasticsearch,
        timeout: int = 600,
) -> None:
    """Waits for the Elasticsearch cluster to be ready.

    Args:
        es: The Elasticsearch client to use.
        timeout: The maximum time to wait for the cluster to become ready.

    Raises:
        TimeoutError: If the cluster does not become ready within the timeout.
    """
    start_time = time.monotonic()
    while time.monotonic() - start_time < timeout:
        try:
            for node in es.transport.node_pool.all():
                node.perform_request("GET", "/", headers={"accept": "application/json"})
            # We were able to perform a request on all nodes, so the cluster is fully ready
            return
        except ConnectionError:
            time.sleep(5)
    raise TimeoutError("Elasticsearch cluster did not become ready within the timeout.")
