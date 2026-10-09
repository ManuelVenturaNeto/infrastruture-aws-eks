#!/usr/bin/env bash
set -euo pipefail

BUCKET="kube-system-experiment-tfstate"
REGION="us-east-1"

if aws s3api head-bucket --bucket "${BUCKET}" 2>/dev/null; then
  echo "State bucket ${BUCKET} already exists."
  exit 0
fi

aws s3api create-bucket --bucket "${BUCKET}" --region "${REGION}"
aws s3api put-bucket-versioning --bucket "${BUCKET}" \
  --versioning-configuration Status=Enabled
