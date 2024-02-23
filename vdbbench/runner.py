import io
import json
import logging
import os
import tarfile
import time
from pathlib import Path

import paramiko
from fabric import Connection

from vdbbench import PROJECT_DIR

logger = logging.getLogger(__name__)


def package_vdbbench():
    """Creates a tarball of all Python files and the requirements.txt file.

    Returns:
        A BytesIO object with the tarball contents.
    """
    buff = io.BytesIO()
    with tarfile.open(mode="w:gz", fileobj=buff) as tar_file:
        for file_path in Path(PROJECT_DIR).rglob("*"):
            if file_path.suffix in [".py"] or file_path.name == "requirements.txt":
                tar_file.add(file_path, arcname=file_path.relative_to(PROJECT_DIR))
    buff.seek(0)
    return buff


def retry_execute_runner(
    name: str,
    config: dict,
    timeout: int = 300,
    interval: int = 5,
) -> dict:
    """Retries the execution of the benchmark on the runner instance until it becomes available or the timeout is reached.

    Args:
        name: The name of the benchmark to run.
        config: The configuration dictionary returned by the deploy method of the benchmark.
        timeout: The maximum time to wait for the runner to become available.
        interval: The time to wait between retries.

    Returns:
        The result of the benchmark execution.
    """
    start_time = time.monotonic()
    while time.monotonic() - start_time < timeout:
        try:
            return execute_runner(name, config)
        except paramiko.ssh_exception.NoValidConnectionsError:
            time.sleep(interval)
    raise TimeoutError("Runner did not become available within the timeout.")


def execute_runner(name: str, config: dict) -> dict:
    """Executes the benchmark with the given name on the runner instance.

    Args:
        name: The name of the benchmark to run.
        config: The configuration dictionary returned by the deploy method of the benchmark.

    Returns:
        The result of the benchmark execution.
    """
    private_key_path = os.environ.get("PRIVATE_KEY_PATH")
    if not private_key_path:
        raise ValueError("PRIVATE_KEY_PATH environment variable must be set")

    host_ip = config["runner_instance_ip"]
    user = "vdbbench"

    conn = Connection(
        host=host_ip,
        user=user,
        connect_kwargs={
            "key_filename": private_key_path,
        },
    )

    with conn:
        package = package_vdbbench()
        remote_tar_path = "/tmp/vdbbench_package.tar.gz"

        conn.put(package, remote_tar_path)
        conn.run(
            f"rm -rf /tmp/vdbbench && \
              mkdir -p /tmp/vdbbench && \
              tar -xzf {remote_tar_path} -C /tmp/vdbbench",
        )

        config_json = json.dumps(config)
        config_json_path = "/tmp/vdbbench/config.json"
        conn.put(io.BytesIO(config_json.encode()), config_json_path)

        conn.run("sudo apt update")
        conn.run("sudo apt install -y python3-pip python3-venv")
        conn.run("python3 -m venv /tmp/vdbbench/venv")
        conn.run(
            f". /tmp/vdbbench/venv/bin/activate && \
              pip install -r /tmp/vdbbench/requirements.txt && \
              cd /tmp/vdbbench && \
              python -m vdbbench run-bench {name} {config_json_path}",
        )

        output_path = "/tmp/vdbbench/output.json"
        if conn.run(f"test -f {output_path}", warn=True).ok:
            return json.loads(conn.run(f"cat {output_path}", hide=True).stdout)
        else:
            raise FileNotFoundError(
                "Benchmark output (output.json) not found on the runner.",
            )
