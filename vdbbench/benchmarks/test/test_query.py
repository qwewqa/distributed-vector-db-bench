import numpy as np

from vdbbench.benchmarks.query_benchmark import QueryBenchmark
from vdbbench.datasets import Dataset
from vdbbench.terraform import DatabaseDeployment, apply_terraform


class TestQuery(QueryBenchmark):
    def run_deploy(
        self, node_count: int = 3, machine_type: str = "n1-standard-1"
    ) -> dict:
        return apply_terraform(
            DatabaseDeployment.RUNNER_ONLY,
            node_count=node_count,
            machine_type=machine_type,
        )

    def init(self, deploy_output: dict):
        pass

    def load_data(self, dataset: Dataset):
        self.dataset = dataset
        self.neighbors_by_vector = {
            tuple(dataset.test[i]): dataset.neighbors[i]
            for i in range(len(dataset.test))
        }

    def prepare_group(self):
        pass

    def prepare_query(self):
        pass

    def query(self, queries: np.ndarray, k: int = 10) -> list[list[int]]:
        return [
            [self.neighbors_by_vector[tuple(query)][i] for i in range(k)]
            for query in queries
        ]
