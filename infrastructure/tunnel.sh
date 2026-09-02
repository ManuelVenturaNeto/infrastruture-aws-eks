#!/usr/bin/env bash
set -euo pipefail

NAME_PREFIX="kube-system-experiment"
REGION="us-east-1"
PORTA_REMOTA=3128
PORTA_LOCAL="${1:-3128}"

exigir_plugin_do_ssm() {
  if command -v session-manager-plugin >/dev/null 2>&1; then
    return
  fi

  echo "session-manager-plugin nao encontrado." >&2
  echo "O aws ssm start-session depende dele. Instale com:" >&2
  echo >&2
  echo "  curl -o /tmp/session-manager-plugin.deb \\" >&2
  echo "    https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" >&2
  echo "  sudo dpkg -i /tmp/session-manager-plugin.deb" >&2
  exit 1
}

instancia_do_bastion() {
  aws ec2 describe-instances \
    --region "${REGION}" \
    --filters "Name=tag:Name,Values=${NAME_PREFIX}-bastion" \
    "Name=instance-state-name,Values=running" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text
}

exigir_plugin_do_ssm

INSTANCIA="$(instancia_do_bastion)"

if [[ -z "${INSTANCIA}" || "${INSTANCIA}" == "None" ]]; then
  echo "Nenhum bastion em estado running." >&2
  echo "Rode 'terraform -chdir=infrastructure/cluster apply' antes." >&2
  exit 1
fi

cat <<TEXTO

Bastion: ${INSTANCIA}
Tunel:   localhost:${PORTA_LOCAL} -> proxy CONNECT do bastion

Deixe este terminal aberto. Em outro terminal:

  export HTTPS_PROXY=http://localhost:${PORTA_LOCAL}
  ./infrastructure/apply.sh spark
  kubectl get nodes

TEXTO

aws ssm start-session \
  --region "${REGION}" \
  --target "${INSTANCIA}" \
  --document-name AWS-StartPortForwardingSession \
  --parameters "portNumber=${PORTA_REMOTA},localPortNumber=${PORTA_LOCAL}"
