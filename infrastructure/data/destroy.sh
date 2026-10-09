#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

terraform -chdir="${HERE}/terraform" init -input=false
terraform -chdir="${HERE}/terraform" destroy -input=false -auto-approve
