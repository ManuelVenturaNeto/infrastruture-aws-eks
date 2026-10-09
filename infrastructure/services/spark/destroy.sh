#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TF_DIR="${HERE}/terraform"
STATE_BUCKET="kube-system-tfstate"
STATE_KEY="services/spark/terraform.tfstate"

cluster_acessivel() {
  kubectl cluster-info >/dev/null 2>&1
}

state_exists() {
  aws s3api head-object --bucket "${STATE_BUCKET}" --key "${STATE_KEY}" >/dev/null 2>&1
}

crd_instalado() {
  kubectl get crd "$1" >/dev/null 2>&1
}

destruir_terraform() {
  if ! state_exists; then
    return
  fi

  terraform -chdir="${TF_DIR}" init -input=false
  terraform -chdir="${TF_DIR}" destroy -input=false -auto-approve
}

if cluster_acessivel; then
  if crd_instalado sparkapplications.sparkoperator.k8s.io; then
    kubectl delete scheduledsparkapplication --all -n spark-jobs --ignore-not-found
    kubectl delete sparkapplication --all -n spark-jobs --ignore-not-found
  fi

  kubectl delete -f "${HERE}/history-server/" --ignore-not-found --wait

  if helm status spark-operator --namespace spark-operator >/dev/null 2>&1; then
    helm uninstall spark-operator --namespace spark-operator --wait
  fi

  kubectl delete -R -f "${HERE}/nodepools/" --ignore-not-found --wait --timeout=30m
fi

destruir_terraform

if cluster_acessivel; then
  kubectl delete -f "${HERE}/namespaces.yaml" --ignore-not-found --wait --timeout=10m
fi
