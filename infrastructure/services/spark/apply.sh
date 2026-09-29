#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OPERATOR_VERSION="2.5.2"

kubectl apply -f "${HERE}/namespaces.yaml"
kubectl apply -f "${HERE}/networkpolicy.yaml"

terraform -chdir="${HERE}/terraform" init -input=false
terraform -chdir="${HERE}/terraform" apply -input=false -auto-approve

kubectl apply -R -f "${HERE}/nodepools/"

helm upgrade --install spark-operator \
  oci://ghcr.io/kubeflow/spark-operator/charts/spark-operator \
  --version "${OPERATOR_VERSION}" \
  --namespace spark-operator \
  --values "${HERE}/operator/helm-values.yaml" \
  --wait

kubectl rollout status deploy/spark-operator-controller -n spark-operator --timeout=5m
kubectl rollout status deploy/spark-operator-webhook -n spark-operator --timeout=5m

kubectl apply -f "${HERE}/history-server/"
kubectl rollout status deploy/spark-history -n spark-history --timeout=15m
