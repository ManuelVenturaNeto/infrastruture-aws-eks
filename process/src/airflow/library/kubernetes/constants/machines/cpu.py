from ...interfaces import Profile
from .. import tolerations

CPU = Profile(
    manifest={
        "spec": {
            "executor": {
                "nodeSelector": {"workload": "spark"},
                "tolerations": [tolerations.SPARK],
            }
        }
    }
)
