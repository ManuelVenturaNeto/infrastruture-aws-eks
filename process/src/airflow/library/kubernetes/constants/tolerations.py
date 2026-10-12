SPARK = {
    "key": "workload",
    "operator": "Equal",
    "value": "spark",
    "effect": "NoSchedule",
}

SPARK_GPU = {
    "key": "workload",
    "operator": "Equal",
    "value": "spark-gpu",
    "effect": "NoSchedule",
}

NVIDIA = {
    "key": "nvidia.com/gpu",
    "operator": "Equal",
    "value": "true",
    "effect": "NoSchedule",
}
