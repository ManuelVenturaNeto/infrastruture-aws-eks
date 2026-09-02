#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OPERATOR_VERSION="2.5.2"

kubectl apply -f "${HERE}/namespaces.yaml"

helm upgrade --install spark-operator \
  oci://ghcr.io/kubeflow/spark-operator/charts/spark-operator \
  --version "${OPERATOR_VERSION}" \
  --namespace spark-operator \
  --values "${HERE}/helm-values.yaml" \
  --wait

kubectl rollout status deploy/spark-operator-controller -n spark-operator --timeout=5m
kubectl rollout status deploy/spark-operator-webhook -n spark-operator --timeout=5m
