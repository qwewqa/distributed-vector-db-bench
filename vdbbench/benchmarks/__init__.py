from typing import Callable

from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.benchmarks.elasticsearch.load_dataset_elasticsearch import (
    LoadDatasetElasticsearch,
)
from vdbbench.benchmarks.elasticsearch.query_elasticsearch import QueryElasticsearch
from vdbbench.benchmarks.elasticsearch.test_elasticsearch import TestElasticsearch

BENCHMARKS: dict[str, Callable[..., Benchmark]] = {
    "elasticsearch-test": TestElasticsearch,
    "elasticsearch-load": LoadDatasetElasticsearch,
    "elasticsearch-query": QueryElasticsearch,
}
