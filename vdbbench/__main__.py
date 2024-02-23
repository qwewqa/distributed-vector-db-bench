import json
import logging
import os
from pathlib import Path

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
    name: str = typer.Argument(..., help="The name of the benchmark to run."),
):
    logger.info(f"Running benchmark for {name}")
    if not os.environ.get("TF_VAR_project"):
        logger.error("Environment variables are not set. Run `. setup.sh` to set them.")
        return
    if name in benchmarks.BENCHMARKS:
        benchmark = benchmarks.BENCHMARKS[name]
        config = benchmark.deploy()
        result = retry_execute_runner(name, config)
        logger.info(result)
    else:
        logger.error(f"Unknown benchmark: {name}")


@app.command(hidden=True)
def run_bench(name: str, config: Path):
    logger.info(f"Running benchmark for {name} with config {config}")
    config_data = json.loads(config.read_text())
    benchmark = benchmarks.BENCHMARKS[name]
    result = benchmark.run(config_data)
    Path("output.json").write_text(json.dumps(result))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app()
