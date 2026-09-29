#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OPERATOR_VERSION="1.2.0"
UI_CHART_VERSION="1.6.5"

kubectl apply -f "${HERE}/namespaces.yaml"
kubectl apply -f "${HERE}/networkpolicy.yaml"
kubectl apply -R -f "${HERE}/nodepools/"

helm upgrade --install strimzi strimzi-kafka-operator \
  --repo https://strimzi.io/charts/ \
  --version "${OPERATOR_VERSION}" \
  --namespace kafka \
  --values "${HERE}/operator/helm-values.yaml" \
  --wait

kubectl rollout status deploy/strimzi-cluster-operator -n kafka --timeout=5m

kubectl apply -f "${HERE}/brokers/"
kubectl wait kafka/kafka -n kafka --for=condition=Ready --timeout=20m

helm upgrade --install kafka-ui kafka-ui \
  --repo https://kafbat.github.io/helm-charts \
  --version "${UI_CHART_VERSION}" \
  --namespace kafka \
  --values "${HERE}/ui/helm-values.yaml" \
  --wait
