#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TF_DIR="${HERE}/terraform"
STATE_BUCKET="kube-system-experiment-tfstate"
STATE_KEY="services/mlflow/terraform.tfstate"

cluster_acessivel() {
  kubectl cluster-info >/dev/null 2>&1
}

state_exists() {
  aws s3api head-object --bucket "${STATE_BUCKET}" --key "${STATE_KEY}" >/dev/null 2>&1
}

esquecer_recursos_do_kubernetes() {
  local recurso
  for recurso in $(terraform -chdir="${TF_DIR}" state list | grep '^kubernetes_' || true); do
    terraform -chdir="${TF_DIR}" state rm "${recurso}"
  done
}

destruir_terraform() {
  if ! state_exists; then
    return
  fi

  terraform -chdir="${TF_DIR}" init -input=false
  if ! cluster_acessivel; then
    esquecer_recursos_do_kubernetes
  fi
  terraform -chdir="${TF_DIR}" destroy -input=false -auto-approve
}

if cluster_acessivel; then
  if helm status mlflow --namespace mlflow >/dev/null 2>&1; then
    helm uninstall mlflow --namespace mlflow --wait
  fi
  kubectl delete -R -f "${HERE}/nodepools/" --ignore-not-found --wait --timeout=30m
fi

destruir_terraform

if cluster_acessivel; then
  kubectl delete -f "${HERE}/namespaces.yaml" --ignore-not-found --wait --timeout=10m
fi
