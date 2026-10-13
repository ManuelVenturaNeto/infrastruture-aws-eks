#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
IMAGES="$(cd "${HERE}/../../../process/src/images" && pwd)"
REGION="us-east-1"
SPARK_TAG="4.2.0"
RAPIDS_TAG="4.2.0-26.08.1"

image_exists() {
  aws ecr describe-images --region "${REGION}" \
    --repository-name "kube-system/$1" \
    --image-ids imageTag="$2" >/dev/null 2>&1
}

push_image() {
  local name="$1" tag="$2" dockerfile="$3"
  local image="${REGISTRY}/kube-system/${name}:${tag}"

  if image_exists "${name}" "${tag}"; then
    return
  fi

  docker build --platform linux/amd64 \
    --file "${IMAGES}/${dockerfile}/Dockerfile" \
    --tag "${image}" "${IMAGES}"
  docker push "${image}"
}

kubectl apply -f "${HERE}/namespaces.yaml"
kubectl apply -f "${HERE}/networkpolicy.yaml"
kubectl apply -f "${HERE}/airflow-rbac.yaml"

terraform -chdir="${HERE}/terraform" init -input=false
terraform -chdir="${HERE}/terraform" apply -input=false -auto-approve

kubectl apply -R -f "${HERE}/nodepools/"

helm upgrade --install spark-operator spark-operator \
  --repo https://kubeflow.github.io/spark-operator \
  --version 2.5.2 \
  --namespace spark-operator \
  --values "${HERE}/operator/helm-values.yaml" \
  --wait

kubectl rollout status deploy/spark-operator-controller -n spark-operator --timeout=5m
kubectl rollout status deploy/spark-operator-webhook -n spark-operator --timeout=5m

kubectl apply -f "${HERE}/history-server/"
kubectl rollout status deploy/spark-history -n spark-history --timeout=15m

REGISTRY="$(aws sts get-caller-identity --query Account --output text).dkr.ecr.${REGION}.amazonaws.com"

aws ecr get-login-password --region "${REGION}" \
  | docker login --username AWS --password-stdin "${REGISTRY}"

push_image spark "${SPARK_TAG}" base-cpu
push_image spark-rapids "${RAPIDS_TAG}" base-gpu-rapids
