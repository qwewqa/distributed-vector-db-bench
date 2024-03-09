from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.benchmarks.elasticsearch.load_dataset_elasticsearch import (
    LoadDatasetElasticsearch,
)
from vdbbench.benchmarks.elasticsearch.test_elasticsearch import TestElasticsearch
from vdbbench.datasets import glove_25d

from vdbbench.benchmarks.neo4j.test_neo4j import TestNeo4j

BENCHMARKS: dict[str, Benchmark] = {
    "elasticsearch-test": TestElasticsearch(),
    "elasticsearch-load-glove-25d": LoadDatasetElasticsearch(glove_25d),
    "neo4j": TestNeo4j(),
}
