#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CHART_VERSION="1.11.7"

kubectl apply -f "${HERE}/namespaces.yaml"
kubectl apply -f "${HERE}/networkpolicy.yaml"

terraform -chdir="${HERE}/terraform" init -input=false
terraform -chdir="${HERE}/terraform" apply -input=false -auto-approve

kubectl apply -R -f "${HERE}/nodepools/"

helm upgrade --install mlflow mlflow \
  --repo https://community-charts.github.io/helm-charts \
  --version "${CHART_VERSION}" \
  --namespace mlflow \
  --values "${HERE}/helm-values.yaml" \
  --timeout 15m \
  --wait
