#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OPERATOR_VERSION="1.2.0"

kubectl apply -f "${HERE}/namespaces.yaml"

helm upgrade --install strimzi strimzi-kafka-operator \
  --repo https://strimzi.io/charts/ \
  --version "${OPERATOR_VERSION}" \
  --namespace kafka \
  --values "${HERE}/helm-values.yaml" \
  --wait

kubectl rollout status deploy/strimzi-cluster-operator -n kafka --timeout=5m
