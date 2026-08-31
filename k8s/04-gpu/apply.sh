#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_VERSION="0.20.0"

helm upgrade --install nvidia-device-plugin nvidia-device-plugin \
  --repo https://nvidia.github.io/k8s-device-plugin \
  --version "${PLUGIN_VERSION}" \
  --namespace kube-system \
  --values "${HERE}/helm-values.yaml" \
  --wait

kubectl get daemonset -n kube-system -l app.kubernetes.io/name=nvidia-device-plugin
