#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CONTEXT="$(cd "${HERE}/.." && pwd)"

NAME_PREFIX="kube-system-experiment"
REGION="us-east-1"

IMAGE="${1:-}"
TAG="${2:-}"

if [[ -z "${IMAGE}" || -z "${TAG}" ]]; then
  echo "uso: build.sh <imagem> <tag>    ex.: build.sh spark 1.0.0" >&2
  exit 1
fi

if [[ ! -f "${HERE}/${IMAGE}/Dockerfile" ]]; then
  echo "Nao existe ${HERE}/${IMAGE}/Dockerfile" >&2
  exit 1
fi

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
REGISTRY="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com"
REPOSITORY="${REGISTRY}/${NAME_PREFIX}/${IMAGE}"

aws ecr get-login-password --region "${REGION}" \
  | docker login --username AWS --password-stdin "${REGISTRY}"

docker build \
  --platform linux/amd64 \
  --file "${HERE}/${IMAGE}/Dockerfile" \
  --tag "${REPOSITORY}:${TAG}" \
  "${CONTEXT}"

docker push "${REPOSITORY}:${TAG}"

printf '\nimage: %s:%s\n' "${REPOSITORY}" "${TAG}"
