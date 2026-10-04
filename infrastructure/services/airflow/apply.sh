#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

kubectl apply -f "${HERE}/namespaces.yaml"
kubectl apply -f "${HERE}/networkpolicy.yaml"

terraform -chdir="${HERE}/terraform" init -input=false
terraform -chdir="${HERE}/terraform" apply -input=false -auto-approve

kubectl apply -R -f "${HERE}/nodepools/"

helm upgrade --install airflow airflow \
  --repo https://airflow.apache.org \
  --namespace airflow \
  --values "${HERE}/helm-values.yaml" \
  --timeout 20m \
  --wait

kubectl apply -f "${HERE}/hpa.yaml"
