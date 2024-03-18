from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.benchmarks.elasticsearch.load_dataset_elasticsearch import (
    LoadDatasetElasticsearch,
)
from vdbbench.benchmarks.elasticsearch.query_elasticsearch import QueryElasticsearch
from vdbbench.benchmarks.elasticsearch.test_elasticsearch import TestElasticsearch
from vdbbench.datasets import fashion_mnist, glove_25d

BENCHMARKS: dict[str, Benchmark] = {
    "elasticsearch-test": TestElasticsearch(),
    "elasticsearch-load-glove-25d": LoadDatasetElasticsearch(glove_25d),
    "elasticsearch-query-glove-25d": QueryElasticsearch(glove_25d),
    "elasticsearch-query-fashion-mnist": QueryElasticsearch(fashion_mnist),
}
