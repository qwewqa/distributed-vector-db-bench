from typing import Callable

from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.benchmarks.elasticsearch.load_dataset_elasticsearch import (
    LoadDatasetElasticsearch,
)
from vdbbench.benchmarks.elasticsearch.query_elasticsearch import QueryElasticsearch
from vdbbench.benchmarks.elasticsearch.test_elasticsearch import TestElasticsearch
from vdbbench.benchmarks.test.test_query import TestQuery

from vdbbench.benchmarks.weaviate.load_dataset_weaviate import LoadDatasetWeaviate
from vdbbench.benchmarks.weaviate.query_weaviate import QueryWeaviate
from vdbbench.benchmarks.weaviate.test_weaviate import TestWeaviate

BENCHMARKS: dict[str, Callable[..., Benchmark]] = {
    "elasticsearch-test": TestElasticsearch,
    "elasticsearch-load": LoadDatasetElasticsearch,
    "elasticsearch-query": QueryElasticsearch,

    "test-query": TestQuery,

    "weaviate-test": TestWeaviate,
    "weaviate-load": LoadDatasetWeaviate,
    "weaviate-query": QueryWeaviate,
}
