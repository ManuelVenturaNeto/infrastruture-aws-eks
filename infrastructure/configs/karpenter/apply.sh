#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
KARPENTER_VERSION="1.14.1"

helm upgrade --install karpenter oci://public.ecr.aws/karpenter/karpenter \
  --version "${KARPENTER_VERSION}" \
  --namespace kube-system \
  --values "${HERE}/helm-values.yaml" \
  --wait

kubectl rollout status deploy/karpenter -n kube-system --timeout=5m
