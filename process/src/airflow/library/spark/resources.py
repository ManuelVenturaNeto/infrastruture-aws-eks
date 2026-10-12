import logging
import os
import shutil
import socket
import subprocess
from pathlib import Path

from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)

CGROUP = Path("/sys/fs/cgroup")
GIB = 1024**3


def read(path: Path) -> str | None:
    try:
        return path.read_text().strip()
    except OSError:
        return None


def cpu_limit() -> float | None:
    value = read(CGROUP / "cpu.max")
    if value is None or value.startswith("max"):
        return None
    quota, period = value.split()
    return int(quota) / int(period)


def memory_limit() -> int | None:
    value = read(CGROUP / "memory.max")
    if value is None or value == "max":
        return None
    return int(value)


def memory_used() -> int | None:
    value = read(CGROUP / "memory.current")
    if value is None:
        return None
    return int(value)


def gpus() -> list[tuple[str, int, int]]:
    if shutil.which("nvidia-smi") is None:
        return []
    output = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.used,memory.total",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    found = []
    for line in output.splitlines():
        name, used, total = (field.strip() for field in line.split(","))
        found.append((name, int(used) * 1024**2, int(total) * 1024**2))
    return found


def snapshot() -> dict:
    return {
        "host": socket.gethostname(),
        "cpu_total": os.cpu_count(),
        "cpu_limit": cpu_limit(),
        "memory_total": os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"),
        "memory_limit": memory_limit(),
        "memory_used": memory_used(),
        "gpus": gpus(),
    }


def gib(value: int | None) -> str:
    return "n/a" if value is None else f"{value / GIB:.1f} GiB"


def describe(role: str, machine: dict) -> str:
    cpu_limit = machine["cpu_limit"]
    cpu = f"{cpu_limit:g}" if cpu_limit is not None else "no limit"
    gpu = (
        ", ".join(
            f"{name} {gib(used)} used of {gib(total)}"
            for name, used, total in machine["gpus"]
        )
        or "none"
    )
    return (
        f"{role} {machine['host']}: "
        f"cpu {cpu} of {machine['cpu_total']} cores | "
        f"memory {gib(machine['memory_used'])} used, "
        f"{gib(machine['memory_limit'])} limit, "
        f"{gib(machine['memory_total'])} total | "
        f"gpu {gpu}"
    )


def executors(spark: SparkSession) -> list[dict]:
    conf = spark.sparkContext.getConf()
    count = int(
        conf.get(
            "spark.dynamicAllocation.initialExecutors",
            conf.get("spark.executor.instances", "1"),
        )
    )
    tasks = count * int(conf.get("spark.executor.cores", "1"))
    found = spark.sparkContext.parallelize(range(tasks), tasks).map(
        lambda _: snapshot()
    )
    return list({machine["host"]: machine for machine in found.collect()}.values())


def log_resources(spark: SparkSession) -> None:
    """Logs CPU, memory and GPU of the driver and of each running executor.

    Each line shows what the container is using now, the limit reserved for it
    and the total of the node; limits only exist inside Kubernetes.

    Args:
        spark: Active Spark session.
    """
    logger.info(describe("driver", snapshot()))

    if spark.sparkContext.master.startswith("local"):
        return

    for machine in executors(spark):
        logger.info(describe("executor", machine))
