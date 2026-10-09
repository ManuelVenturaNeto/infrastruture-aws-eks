#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="kube-system-eks"
REGION="us-east-1"
HERE="$(cd "$(dirname "$0")" && pwd)"
TF_DIR="${HERE}/cluster"
DATA_DIR="${HERE}/data"
SERVICES="${HERE}/services"
TIMEOUT_DRENAGEM=3600

titulo() {
  printf '\n==> %s\n' "$1"
}

usage() {
  echo "usage: destroy.sh [--include-lake]"
  echo
  echo "Destroys every service and the base. The data lake and the Terraform state"
  echo "bucket are kept."
  echo
  echo "  --include-lake   also destroys the data lake, with all of its content"
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

  titulo "VolumeSnapshots (viram snapshots EBS, apagados no fim pela tag do cluster)"
  kubectl get volumesnapshot -A
}

destruir_servicos() {
  local caminho

  for caminho in "${SERVICES}"/*/; do
    titulo "Servico $(basename "${caminho}")"
    "${caminho}destroy.sh"
  done
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
  terraform -chdir="${TF_DIR}" destroy -input=false -auto-approve
}

destroy_lake() {
  titulo "Destroying the data lake"
  "${DATA_DIR}/destroy.sh"
}

warn_lake_kept() {
  titulo "Data lake kept"
  echo "s3://kube-system-lake still holds the data."
  echo "To destroy it as well: ${0} --include-lake"
}

apagar_orfaos() {
  local volume snapshot
  local filtro="Name=tag:kubernetes.io/cluster/${CLUSTER_NAME},Values=owned"

  titulo "Apagando snapshots EBS criados pelo cluster"
  for snapshot in $(aws ec2 describe-snapshots --region "${REGION}" --owner-ids self \
    --filters "${filtro}" --query 'Snapshots[].SnapshotId' --output text); do
    echo "${snapshot}"
    aws ec2 delete-snapshot --region "${REGION}" --snapshot-id "${snapshot}"
  done

  titulo "Apagando volumes EBS criados pelo cluster"
  for volume in $(aws ec2 describe-volumes --region "${REGION}" \
    --filters "${filtro}" Name=status,Values=available \
    --query 'Volumes[].VolumeId' --output text); do
    echo "${volume}"
    aws ec2 delete-volume --region "${REGION}" --volume-id "${volume}"
  done
}

listar_restantes() {
  titulo "Volumes EBS e snapshots que continuam na conta"

  echo
  echo "Volumes EBS soltos:"
  aws ec2 describe-volumes --region "${REGION}" --output table \
    --filters Name=status,Values=available \
    --query 'Volumes[].{Volume:VolumeId,GB:Size,Criado:CreateTime}'

  echo
  echo "Snapshots:"
  aws ec2 describe-snapshots --region "${REGION}" --owner-ids self --output table \
    --query 'Snapshots[].{Snapshot:SnapshotId,GB:VolumeSize,Criado:StartTime}'

  echo
  echo "O que aparecer acima nao tem a tag do cluster e nao foi apagado."
}

DESTROY_LAKE=false

case "${1:-}" in
  "") ;;
  --include-lake) DESTROY_LAKE=true ;;
  -h | --help)
    usage
    exit 0
    ;;
  *)
    usage >&2
    exit 1
    ;;
esac

titulo "Destruindo o cluster ${CLUSTER_NAME} e tudo que roda nele"

if cluster_acessivel; then
  avisar_sobre_o_que_o_terraform_ignora
  destruir_servicos
  remover_aplicacoes
  remover_nodepools
  esperar_maquinas_encerrarem
else
  titulo "Cluster inacessivel, pulando a limpeza de dentro dele"
  destruir_servicos
fi

destruir_infraestrutura

if [[ "${DESTROY_LAKE}" == true ]]; then
  destroy_lake
else
  warn_lake_kept
fi

apagar_orfaos
listar_restantes
