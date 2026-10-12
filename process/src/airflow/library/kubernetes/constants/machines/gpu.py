from ...interfaces import Profile
from .. import tolerations
from ..cluster import RAPIDS_IMAGE

GPU = Profile(
    manifest={
        "spec": {
            "image": RAPIDS_IMAGE,
            "sparkConf": {
                "spark.kubernetes.driverEnv.SPARK_GPU": "true",
                "spark.executor.resource.gpu.amount": "1",
                "spark.executor.resource.gpu.vendor": "nvidia.com",
                "spark.executor.resource.gpu.discoveryScript": "/opt/spark/examples/src/main/scripts/getGpusResources.sh",
            },
            "executor": {
                "gpu": {"name": "nvidia.com/gpu", "quantity": 1},
                "nodeSelector": {"workload": "spark-gpu"},
                "tolerations": [tolerations.SPARK_GPU, tolerations.NVIDIA],
            },
        }
    }
)
