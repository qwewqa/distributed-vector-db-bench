from time import perf_counter

import redis
import redis.exceptions

from vdbbench.benchmarks.benchmark import Benchmark
from vdbbench.terraform import DatabaseDeployment, apply_terraform


class TestRedis(Benchmark):
    def deploy(self):
        return apply_terraform(DatabaseDeployment.REDIS)

    def run(self, deploy_output: dict) -> dict:
        start_time = perf_counter()
        while perf_counter() - start_time < 300:
            try:
                client = redis.RedisCluster(
                    host=deploy_output["db_instance_names"][0],
                    port=7000,
                    decode_responses=True,
                )
                client.ping()
                break
            except redis.exceptions.RedisError:
                pass
        else:
            return {
                "status": "failure",
                "detail": "Could not connect to Redis cluster.",
            }

        client.set("key", "value")
        value = client.getdel("key")

        if value == "value":
            return {
                "status": "success",
                "detail": "Key set and retrieved successfully.",
            }
        else:
            return {
                "status": "failure",
                "detail": f"Retrieved value does not match the set value, got {value}.",
            }
