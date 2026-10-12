from ...interfaces import Profile
from .. import tolerations

CPU = Profile(
    manifest={
        "spec": {
            "executor": {
                "nodeSelector": {
                    "workload": "spark",
                    "karpenter.sh/capacity-type": "spot",
                },
                "tolerations": [tolerations.SPARK],
            }
        }
    }
)
