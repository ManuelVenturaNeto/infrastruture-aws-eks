#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="kube-system-experiment-eks"
REGION="us-east-1"
HERE="$(cd "$(dirname "$0")" && pwd)"
TF_DIR="${HERE}/cluster"
CONFIGS="${HERE}/configs"

titulo() {
  printf '\n==> %s\n' "$1"
}

nodepools_disponiveis() {
  local caminho
  for caminho in "${CONFIGS}"/nodepools/*/; do
    basename "${caminho}"
  done | sort
}

uso() {
  echo "uso: apply.sh [nodepool ...]"
  echo
  echo "Sem argumentos aplica todos os NodePools. Com argumentos, apenas os citados."
  echo
  echo "Disponiveis:"
  nodepools_disponiveis | sed 's/^/  /'
}

validar_nodepools() {
  local disponiveis nome
  disponiveis="$(nodepools_disponiveis)"

  for nome in "${NODEPOOLS[@]}"; do
    if ! grep -qxF "${nome}" <<<"${disponiveis}"; then
      echo "NodePool desconhecido: ${nome}" >&2
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
  terraform -chdir="${TF_DIR}" apply -input=false
}

gerar_kubeconfig() {
  titulo "Gerando o kubeconfig"
  aws eks update-kubeconfig --region "${REGION}" --name "${CLUSTER_NAME}"
}

exigir_acesso_ao_cluster() {
  if kubectl cluster-info >/dev/null 2>&1; then
    return
  fi

  cat >&2 <<TEXTO

A API do EKS nao respondeu.

Este cluster sobe com endpoint_public_access = false: a API so atende de dentro
da VPC. A infraestrutura ja foi criada, inclusive o bastion. Falta o tunel.

Em outro terminal:

  ./infrastructure/tunnel.sh

Depois, aqui:

  export HTTPS_PROXY=http://localhost:3128
  ${0} ${NODEPOOLS[*]}

O terraform apply e idempotente: rodar de novo nao recria nada.
TEXTO
  exit 1
}

instalar_plataforma() {
  titulo "Karpenter"
  "${CONFIGS}/karpenter/apply.sh"

  titulo "StorageClass default do cluster"
  kubectl apply -f "${CONFIGS}/storage/"
}

instalar_operators() {
  titulo "Spark Operator"
  "${CONFIGS}/operators/spark/apply.sh"

  titulo "Strimzi, o operator do Kafka"
  "${CONFIGS}/operators/kafka/apply.sh"
}

aplicar_nodepools() {
  local nome

  for nome in "${NODEPOOLS[@]}"; do
    if [[ "${nome}" == "spark-gpu" ]]; then
      titulo "Device plugin da NVIDIA, exigido pelo NodePool spark-gpu"
      "${CONFIGS}/gpu/apply.sh"
    fi

    titulo "NodePool ${nome}"
    kubectl apply -f "${CONFIGS}/nodepools/${nome}/"
  done
}

resumo() {
  titulo "NodePools registrados"
  kubectl get nodepools

  titulo "Maquinas de pe"
  kubectl get nodes -L role -L workload -L karpenter.sh/capacity-type

  titulo "Nenhuma maquina de workload sobe agora"
  echo "O Karpenter so cria EC2 quando existir pod Pending que precise dela."
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  uso
  exit 0
fi

NODEPOOLS=("$@")

if [[ ${#NODEPOOLS[@]} -eq 0 ]]; then
  mapfile -t NODEPOOLS < <(nodepools_disponiveis)
fi

validar_nodepools
criar_infraestrutura
gerar_kubeconfig
exigir_acesso_ao_cluster
instalar_plataforma
instalar_operators
aplicar_nodepools
resumo
