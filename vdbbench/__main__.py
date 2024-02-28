import json
import logging
import os
import time
import traceback
from pathlib import Path
from typing import Annotated

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
    name: Annotated[
        str,
        typer.Argument(
            help="The name of the benchmark to run.",
        ),
    ],
):
    logger.info(f"Running benchmark for {name}")
    if not os.environ.get("TF_VAR_project"):
        logger.error("Environment variables are not set. Run `. setup.sh` to set them.")
        return
    if name in benchmarks.BENCHMARKS:
        benchmark = benchmarks.BENCHMARKS[name]
        config = benchmark.deploy()
        results = retry_execute_runner(name, config)
        logger.info(results)
        save_results(name, results)
    else:
        logger.error(f"Unknown benchmark: {name}")


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


@app.command(hidden=True)
def run_bench(name: str, config: Path):
    logger.info(f"Running benchmark for {name} with config {config}")
    config_data = json.loads(config.read_text())
    benchmark = benchmarks.BENCHMARKS[name]
    try:
        result = benchmark.run(config_data)
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
