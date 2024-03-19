from abc import ABC, abstractmethod


class Benchmark(ABC):
    @abstractmethod
    def deploy(self) -> dict:
        """Deploys the the terraform resources for the benchmark.

        Returns:
            A dictionary containing the configuration for the benchmark, typically the terraform output values.
            Must contain a "runner_instance_ip" key with the IP address string of the runner instance.
        """
        pass

    @abstractmethod
    def run(self, deploy_output: dict) -> dict:
        """Runs the benchmark.

        This runs on the runner instance on the deployed module.

        Args:
            deploy_output: The output dictionary returned by the deploy method.

        Returns:
            A dictionary containing the results of the benchmark.
        """
        pass
