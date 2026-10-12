REPOSITORY = "https://github.com/ManuelVenturaNeto/k8s.git"
BRANCH = "main"
CHECKOUT = "/opt/spark/code"
ROOT = f"{CHECKOUT}/repo/process/src/airflow"

GIT_SYNC = {
    "name": "git-sync",
    "image": "registry.k8s.io/git-sync/git-sync:v4.4.2",
    "args": [
        f"--repo={REPOSITORY}",
        f"--ref={BRANCH}",
        f"--root={CHECKOUT}",
        "--link=repo",
        "--depth=1",
        "--one-time",
    ],
    "volumeMounts": [{"name": "code", "mountPath": CHECKOUT}],
}

CODE = {
    "initContainers": [GIT_SYNC],
    "volumeMounts": [{"name": "code", "mountPath": CHECKOUT}],
    "env": [{"name": "PYTHONPATH", "value": ROOT}],
}
