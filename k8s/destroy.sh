#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="kube-system-experiment-eks"
REGION="us-east-1"
TF_DIR="$(cd "$(dirname "$0")" && pwd)/01-cluster"
TIMEOUT_DRENAGEM=3600

titulo() {
  printf '\n==> %s\n' "$1"
}

confirmar() {
  titulo "Destruir o cluster ${CLUSTER_NAME} e tudo que roda nele"
  echo "Volumes com reclaimPolicy Retain nao serao apagados, apenas listados no final."
  echo
  read -r -p "Digite o nome do cluster para confirmar: " resposta
  if [[ "${resposta}" != "${CLUSTER_NAME}" ]]; then
    echo "Abortado."
    exit 1
  fi
}

cluster_acessivel() {
  kubectl cluster-info >/dev/null 2>&1
}

namespaces_de_aplicacao() {
  kubectl get ns -o name \
    | cut -d/ -f2 \
    | grep -vxE 'kube-system|kube-public|kube-node-lease' || true
}

maquinas_do_karpenter() {
  kubectl get nodes -l karpenter.sh/nodepool --no-headers 2>/dev/null | wc -l | tr -d ' '
}

avisar_sobre_o_que_o_terraform_ignora() {
  titulo "Services LoadBalancer (o ELB deles nao pertence ao Terraform)"
  kubectl get svc -A --field-selector spec.type=LoadBalancer

  titulo "VolumeSnapshots (viram snapshots EBS e continuam cobrados)"
  kubectl get volumesnapshot -A
}

remover_aplicacoes() {
  for ns in $(namespaces_de_aplicacao); do
    titulo "Removendo workloads e PVCs do namespace ${ns}"
    kubectl delete all --all -n "${ns}" --ignore-not-found
    kubectl delete pvc --all -n "${ns}" --ignore-not-found
  done
}

remover_nodepools() {
  titulo "Removendo NodePools e EC2NodeClasses"
  kubectl delete nodepool --all --ignore-not-found
  kubectl delete ec2nodeclass --all --ignore-not-found
}

esperar_maquinas_encerrarem() {
  titulo "Aguardando o Karpenter encerrar as maquinas"
  local limite=$((SECONDS + TIMEOUT_DRENAGEM))
  local restantes

  while true; do
    restantes="$(maquinas_do_karpenter)"

    if [[ "${restantes}" -eq 0 ]]; then
      echo "Nenhuma maquina restante."
      return
    fi

    if [[ "${SECONDS}" -gt "${limite}" ]]; then
      echo "Timeout com ${restantes} maquina(s) de pe." >&2
      echo "Inspecione 'kubectl get nodeclaims' antes de seguir." >&2
      exit 1
    fi

    echo "${restantes} maquina(s) restante(s)..."
    sleep 15
  done
}

destruir_infraestrutura() {
  titulo "terraform destroy"
  terraform -chdir="${TF_DIR}" destroy
}

listar_orfaos() {
  titulo "Sobreviveram ao destroy e continuam sendo cobrados"

  echo
  echo "Volumes EBS:"
  aws ec2 describe-volumes --region "${REGION}" --output table \
    --filters Name=status,Values=available \
    --query 'Volumes[].{Volume:VolumeId,GB:Size,Criado:CreateTime}'

  echo
  echo "Snapshots:"
  aws ec2 describe-snapshots --region "${REGION}" --owner-ids self --output table \
    --query 'Snapshots[].{Snapshot:SnapshotId,GB:VolumeSize,Criado:StartTime}'

  echo
  echo "Nada acima foi apagado. Para remover um volume:"
  echo "  aws ec2 delete-volume --region ${REGION} --volume-id vol-xxxxxxxx"
}

confirmar

if cluster_acessivel; then
  avisar_sobre_o_que_o_terraform_ignora
  remover_aplicacoes
  remover_nodepools
  esperar_maquinas_encerrarem
else
  titulo "Cluster inacessivel, pulando a limpeza de dentro dele"
fi

destruir_infraestrutura
listar_orfaos
