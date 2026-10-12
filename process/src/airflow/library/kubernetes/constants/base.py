from ..interfaces import Profile
from . import tolerations
from .cluster import EVENT_LOG, NAMESPACE, SPARK_IMAGE
from .repository import CODE

BASE = Profile(
    manifest={
        "apiVersion": "sparkoperator.k8s.io/v1beta2",
        "kind": "SparkApplication",
        "metadata": {"namespace": NAMESPACE},
        "spec": {
            "type": "Python",
            "mode": "cluster",
            "image": SPARK_IMAGE,
            "imagePullPolicy": "IfNotPresent",
            "sparkVersion": "4.2.0",
            "restartPolicy": {"type": "Never"},
            "volumes": [{"name": "code", "emptyDir": {}}],
            "sparkConf": {
                "spark.hadoop.fs.s3a.aws.credentials.provider": "software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider",
                "spark.eventLog.enabled": "true",
                "spark.eventLog.dir": EVENT_LOG,
            },
            "driver": {
                **CODE,
                "cores": 1,
                "memory": "2g",
                "serviceAccount": "spark",
                "annotations": {"karpenter.sh/do-not-disrupt": "true"},
                "nodeSelector": {
                    "workload": "spark",
                    "karpenter.sh/capacity-type": "on-demand",
                },
                "tolerations": [tolerations.SPARK],
            },
            "executor": CODE,
        },
    }
)
