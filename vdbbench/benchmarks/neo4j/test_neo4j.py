import traceback

from elasticsearch import ConnectionError

from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.benchmarks.elasticsearch.common import (
    create_elasticsearch_client,
    wait_for_elasticsearch_cluster,
)
from vdbbench.terraform import DatabaseDeployment, apply_terraform


class TestNeo4j(Benchmark):
    pass