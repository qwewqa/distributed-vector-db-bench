from vdbbench.benchmarks.benchmark import Benchmark

from vdbbench.benchmarks.elasticsearch.load_dataset_elasticsearch import LoadDatasetElasticsearch
from vdbbench.benchmarks.weaviate.load_dataset_weaviate import LoadDatasetWeaviate

from vdbbench.benchmarks.elasticsearch.test_elasticsearch import TestElasticsearch
from vdbbench.benchmarks.weaviate.test_weaviate import TestWeaviate

from vdbbench.datasets import glove_25d


BENCHMARKS: dict[str, Benchmark] = {
    "elasticsearch-test": TestElasticsearch(),
    "elasticsearch-load-glove-25d": LoadDatasetElasticsearch(glove_25d),

    "weaviate-test": TestWeaviate(),
    "weaviate-load-glove-25d": LoadDatasetWeaviate(glove_25d),
}
