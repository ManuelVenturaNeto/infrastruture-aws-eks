#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
KARPENTER_VERSION="1.14.1"
SPOT_ROLE="AWSServiceRoleForEC2Spot"

if ! aws iam get-role --role-name "${SPOT_ROLE}" >/dev/null 2>&1; then
  aws iam create-service-linked-role --aws-service-name spot.amazonaws.com
fi

helm upgrade --install karpenter oci://public.ecr.aws/karpenter/karpenter \
  --version "${KARPENTER_VERSION}" \
  --namespace kube-system \
  --values "${HERE}/helm-values.yaml" \
  --wait

kubectl rollout status deploy/karpenter -n kube-system --timeout=5m
