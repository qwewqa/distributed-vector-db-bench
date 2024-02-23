from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.benchmarks.elasticsearch.test_elasticsearch import TestElasticsearch

BENCHMARKS: dict[str, Benchmark] = {
    "test-elasticsearch": TestElasticsearch(),
}
