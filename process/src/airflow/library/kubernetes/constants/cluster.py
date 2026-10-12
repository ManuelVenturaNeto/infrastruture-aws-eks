import os

NAMESPACE = "spark-jobs"
REGISTRY = f"{os.environ['ECR_REGISTRY']}/kube-system"
LAKE = "s3a://kube-system-lake"
EVENT_LOG = "s3a://kube-system-spark/event-logs/"
OVERHEAD_FACTOR = 0.4

SPARK_IMAGE = f"{REGISTRY}/spark:4.2.0"
RAPIDS_IMAGE = f"{REGISTRY}/spark-rapids:4.2.0-26.08.1"
