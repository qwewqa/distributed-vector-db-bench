import json
import logging
import os
import time
import traceback
from pathlib import Path
from typing import Annotated, Optional

import typer

from vdbbench import benchmarks
from vdbbench.runner import retry_execute_runner
from vdbbench.terraform import destroy_all_terraform

logger = logging.getLogger(__name__)
app = typer.Typer()


@app.command(
    help="Destroy all resources created by the benchmarks.",
)
def destroy_all():
    destroy_all_terraform()


@app.command(
    help="Run a benchmark.",
)
def run(
    benchmark_name: Annotated[
        Optional[str],
        typer.Option(
            "--benchmark",
            help="The name of the benchmark to run.",
        ),
    ] = None,
    config_path: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            help="The path to the config file for the benchmark.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    args: Annotated[
        Optional[list[str]],
        typer.Argument(
            help="Additional arguments to pass to the benchmark, in the form `key=value`. The key can be a nested key, separated by dots, and the value will be parsed as JSON.",
        ),
    ] = None,
):
    if benchmark_name is None and config_path is None:
        logger.error("No benchmark specified.")
        return
    if config_path is not None:
        config = json.loads(config_path.read_text())
        if benchmark_name is not None:
            logger.error("Both name and config file specified.")
            return
        benchmark_name = config["benchmark"]
    else:
        config = {"benchmark": benchmark_name, "config": {}}
    if args:
        for arg in args:
            key, value = arg.split("=")
            if key == "":
                config["config"] = json.loads(value)
            else:
                key_parts = key.split(".")
                current = config["config"]
                for part in key_parts[:-1]:
                    current = current.setdefault(part, {})
                current[key_parts[-1]] = json.loads(value)
    logger.info(f"Running benchmark for {benchmark_name}")
    if not os.environ.get("TF_VAR_project"):
        logger.error("Environment variables are not set. Run `. setup.sh` to set them.")
        return
    if benchmark_name in benchmarks.BENCHMARKS:
        benchmark = benchmarks.BENCHMARKS[benchmark_name](**config["config"])
        deploy_result = benchmark.deploy()
        results = retry_execute_runner(benchmark_name, config, deploy_result)
        logger.info(results)
        save_results(benchmark_name, results)
    else:
        logger.error(f"Unknown benchmark: {benchmark_name}")


def save_results(name: str, results: dict):
    output_path = Path("results")
    output_path.mkdir(exist_ok=True)
    output_file = output_path / f"{name}_{time.strftime('%Y%m%d-%H%M%S')}.json"
    output_file.write_text(json.dumps(results, indent=2))
    logger.info(f"Results saved to {output_file}")


@app.command(
    name="list",
    help="List available benchmarks.",
)
def list_benchmarks():
    print("Available benchmarks:")
    for name in benchmarks.BENCHMARKS:
        print(f"  {name}")


@app.command(
    name="plot-recall-latency",
    help="Plot recall-latency tradeoff for a query result.",
)
def plot_query_results(
    data: Annotated[
        Path,
        typer.Argument(
            help="The path to the JSON file containing the query results.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
):
    data = json.loads(data.read_text())
    try:
        from vdbbench.plot.query_plot import plot_recall_latency
    except ImportError:
        logger.error(
            "Plotting is not available, ensure that the required packages are installed."
        )
        return
    plot_recall_latency(data)


@app.command(hidden=True)
def run_bench(name: str, config_path: Path):
    logger.info(f"Running benchmark for {name} with config {config_path}")
    config = json.loads(config_path.read_text())
    benchmark = benchmarks.BENCHMARKS[name](**config["config"])
    try:
        result = benchmark.run(config["deploy_outputs"])
    except Exception as e:
        result = {
            "status": "failure",
            "detail": f"Run failed with error: {e}",
            "traceback": f"{traceback.format_exc()}",
        }
    Path("output.json").write_text(json.dumps(result))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app()
