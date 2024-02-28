from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.benchmarks.elasticsearch.load_dataset_elasticsearch import (
    LoadDatasetElasticsearch,
)
from vdbbench.benchmarks.elasticsearch.test_elasticsearch import TestElasticsearch
from vdbbench.datasets import glove_25d

BENCHMARKS: dict[str, Benchmark] = {
    "elasticsearch-test": TestElasticsearch(),
    "elasticsearch-load-glove-25d": LoadDatasetElasticsearch(glove_25d),
}
