import json
from pathlib import Path
import typer
import logging
from vdbbench import benchmarks
from vdbbench.runner import retry_execute_runner

from vdbbench.terraform import destroy_all_terraform

logger = logging.getLogger(__name__)
app = typer.Typer()


@app.command()
def destroy_all():
    destroy_all_terraform()


@app.command()
def run(name: str):
    logger.info(f"Running benchmark for {name}")
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
