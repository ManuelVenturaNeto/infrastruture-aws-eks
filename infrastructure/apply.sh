#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="kube-system-experiment-eks"
REGION="us-east-1"
HERE="$(cd "$(dirname "$0")" && pwd)"
TF_DIR="${HERE}/cluster"
CONFIGS="${HERE}/configs"
SERVICES="${HERE}/services"

titulo() {
  printf '\n==> %s\n' "$1"
}

servicos_disponiveis() {
  local caminho
  for caminho in "${SERVICES}"/*/; do
    basename "${caminho}"
  done | sort
}

uso() {
  echo "uso: apply.sh [servico ...]"
  echo
  echo "Sem argumentos sobe apenas a base: EKS, Karpenter, StorageClass e o device"
  echo "plugin da GPU. Com argumentos sobe a base e os servicos citados, completos."
  echo
  echo "Disponiveis:"
  servicos_disponiveis | sed 's/^/  /'
}

validar_servicos() {
  local disponiveis nome
  disponiveis="$(servicos_disponiveis)"

  for nome in "${SERVICOS[@]}"; do
    if ! grep -qxF "${nome}" <<<"${disponiveis}"; then
      echo "Servico desconhecido: ${nome}" >&2
      echo >&2
      uso >&2
      exit 1
    fi
  done
}

criar_infraestrutura() {
  titulo "terraform init"
  terraform -chdir="${TF_DIR}" init -input=false

  titulo "terraform apply"
  terraform -chdir="${TF_DIR}" apply -input=false -auto-approve
}

gerar_kubeconfig() {
  titulo "Gerando o kubeconfig"
  aws eks update-kubeconfig --region "${REGION}" --name "${CLUSTER_NAME}" --alias "${CLUSTER_NAME}"
}

instalar_plataforma() {
  titulo "Karpenter"
  "${CONFIGS}/karpenter/apply.sh"

  titulo "StorageClass default do cluster"
  kubectl apply -f "${CONFIGS}/storage/"

  titulo "Device plugin da NVIDIA"
  "${CONFIGS}/gpu/apply.sh"
}

subir_servicos() {
  local nome

  for nome in "${SERVICOS[@]}"; do
    titulo "Servico ${nome}"
    if ! "${SERVICES}/${nome}/apply.sh"; then
      titulo "Servico ${nome} falhou. Desfazendo para nao deixar pela metade"
      "${SERVICES}/${nome}/destroy.sh"
      exit 1
    fi
  done
}

resumo() {
  titulo "NodePools registrados"
  kubectl get nodepools

  titulo "Maquinas de pe"
  kubectl get nodes -L role -L workload -L karpenter.sh/capacity-type

  if [[ ${#SERVICOS[@]} -eq 0 ]]; then
    titulo "Nenhuma maquina de workload sobe agora"
    echo "Nenhum servico foi pedido. Para subir um: ${0} <servico ...>"
    return
  fi

  titulo "Releases instalados"
  helm list -A
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  uso
  exit 0
fi

SERVICOS=("$@")

validar_servicos
criar_infraestrutura
gerar_kubeconfig
instalar_plataforma
subir_servicos
resumo
