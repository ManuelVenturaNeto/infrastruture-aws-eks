from pathlib import Path
from types import ModuleType

from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import (
    SparkKubernetesOperator,
)
from airflow.sdk import DAG

from .constants.base import BASE
from .constants.cluster import LAKE, NAMESPACE, OVERHEAD_FACTOR
from .constants.machines import CPU, GPU
from .constants.repository import ROOT
from .interfaces import Cpu, Gpu, Instances, Profile

PACKAGES = Path(__file__).resolve().parents[2]


def merge(base: dict, overlay: dict) -> dict:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def spark_job(
    dag: DAG,
    task_id: str,
    job: ModuleType,
    sources: dict[str, str],
    targets: dict[str, str],
    cpu: Cpu = Cpu.MEDIUM,
    gpu: Gpu | None = None,
    instances: Instances = Instances.SMALL,
) -> SparkKubernetesOperator:
    """Builds the task that submits a job as a SparkApplication.

    Args:
        dag: DAG that owns the task; its dag_id names the dataset in the lake.
        task_id: Task name, also used in the SparkApplication name.
        job: Package holding the job's main.py.
        sources: Job argument name to input table inside the dataset folder;
            each entry becomes --name <lake>/<dag_id>/<table>.
        targets: Job argument name to output table, passed the same way.
        cpu: Cores and memory of each executor.
        gpu: Minimum GPU memory of each executor's node, which also picks
            the RAPIDS image; None runs on CPU only.
        instances: Executor range for dynamic allocation.

    Returns:
        The operator bound to the DAG.
    """
    selected = [BASE, CPU]

    overhead = int(cpu.memory * 1024 * OVERHEAD_FACTOR)

    if gpu is not None:
        selected.append(GPU)
        selected.append(
            Profile(
                manifest={
                    "spec": {
                        "sparkConf": {
                            "spark.task.resource.gpu.amount": str(1 / cpu.cores),
                            "spark.rapids.memory.pinnedPool.size": f"{overhead // 2}m",
                        },
                        "executor": {
                            "affinity": {
                                "nodeAffinity": {
                                    "requiredDuringSchedulingIgnoredDuringExecution": {
                                        "nodeSelectorTerms": [
                                            {
                                                "matchExpressions": [
                                                    {
                                                        "key": "karpenter.k8s.aws/instance-gpu-memory",
                                                        "operator": "Gt",
                                                        "values": [
                                                            str(gpu.memory * 1024 - 1)
                                                        ],
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                    }
                }
            )
        )

    main = Path(job.__file__).resolve().parent.relative_to(PACKAGES) / "main.py"

    selected.append(
        Profile(
            manifest={
                "metadata": {"name": f"{dag.dag_id}-{task_id}".replace("_", "-")},
                "spec": {
                    "mainApplicationFile": f"local://{ROOT}/{main.as_posix()}",
                    "arguments": [
                        argument
                        for name, table in (sources | targets).items()
                        for argument in (f"--{name}", f"{LAKE}/{dag.dag_id}/{table}")
                    ],
                    "sparkConf": {
                        "spark.kubernetes.driverEnv.SPARK_APP_NAME": f"{dag.dag_id}_{task_id}"
                    },
                    "executor": {
                        "cores": cpu.cores,
                        "memory": f"{cpu.memory}g",
                        "memoryOverhead": f"{overhead}m",
                    },
                    "dynamicAllocation": {
                        "enabled": True,
                        "shuffleTrackingEnabled": True,
                        "initialExecutors": instances.minimum,
                        "minExecutors": instances.minimum,
                        "maxExecutors": instances.maximum,
                    },
                },
            }
        )
    )

    manifest: dict = {}

    for profile in selected:
        manifest = merge(manifest, profile.manifest)

    return SparkKubernetesOperator(
        task_id=task_id,
        dag=dag,
        namespace=NAMESPACE,
        template_spec=manifest,
    )
