import time

from elasticsearch import ConnectionError, Elasticsearch


def create_elasticsearch_client(
    config: dict,
) -> Elasticsearch:
    """Creates an Elasticsearch client from the configuration.

    Args:
        config: The output from the Terraform module for the Elasticsearch deployment.

    Returns:
        An Elasticsearch client.
    """
    return Elasticsearch(
        hosts=[
            {"host": host, "port": 9200, "scheme": "http"}
            for host in config["elasticsearch_instance_names"]
        ]
    )


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
            es.cluster.health(wait_for_status="green")
            return
        except ConnectionError:
            time.sleep(5)
    raise TimeoutError("Elasticsearch cluster did not become ready within the timeout.")
