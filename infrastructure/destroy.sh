#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="kube-system-experiment-eks"
REGION="us-east-1"
TF_DIR="$(cd "$(dirname "$0")" && pwd)/cluster"
TIMEOUT_DRENAGEM=3600
TIMEOUT_BROKERS=900

titulo() {
  printf '\n==> %s\n' "$1"
}

confirmar() {
  titulo "Destruir o cluster ${CLUSTER_NAME} e tudo que roda nele"
  echo "Volumes com reclaimPolicy Retain nao serao apagados, apenas listados no final."
  echo "As imagens nos repositorios ECR SERAO apagadas junto com eles."
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

crd_instalado() {
  kubectl get crd "$1" >/dev/null 2>&1
}

release_instalado() {
  helm status "$1" --namespace "$2" >/dev/null 2>&1
}

namespaces_de_aplicacao() {
  kubectl get ns -o name \
    | cut -d/ -f2 \
    | grep -vxE 'kube-system|kube-public|kube-node-lease' || true
}

maquinas_do_karpenter() {
  kubectl get nodes -l karpenter.sh/nodepool --no-headers 2>/dev/null | wc -l | tr -d ' '
}

pods_do_kafka() {
  kubectl get pods -n kafka -l strimzi.io/kind=Kafka --no-headers 2>/dev/null | wc -l | tr -d ' '
}

avisar_sobre_o_que_o_terraform_ignora() {
  titulo "Services LoadBalancer (o ELB deles nao pertence ao Terraform)"
  kubectl get svc -A --field-selector spec.type=LoadBalancer

  titulo "VolumeSnapshots (viram snapshots EBS e continuam cobrados)"
  kubectl get volumesnapshot -A
}

remover_jobs_do_spark() {
  if ! crd_instalado sparkapplications.sparkoperator.k8s.io; then
    return
  fi

  titulo "Removendo SparkApplications"
  kubectl delete scheduledsparkapplication --all -A --ignore-not-found
  kubectl delete sparkapplication --all -A --ignore-not-found
}

remover_clusters_do_kafka() {
  if ! crd_instalado kafkas.kafka.strimzi.io; then
    return
  fi

  titulo "Removendo recursos do Strimzi"
  kubectl delete kafkaconnect --all -A --ignore-not-found
  kubectl delete kafkatopic --all -A --ignore-not-found
  kubectl delete kafkauser --all -A --ignore-not-found
  kubectl delete kafka --all -A --ignore-not-found
  kubectl delete kafkanodepool --all -A --ignore-not-found

  esperar_brokers_encerrarem
}

esperar_brokers_encerrarem() {
  titulo "Aguardando o Strimzi encerrar os brokers"
  local limite=$((SECONDS + TIMEOUT_BROKERS))
  local restantes

  while true; do
    restantes="$(pods_do_kafka)"

    if [[ "${restantes}" -eq 0 ]]; then
      echo "Nenhum broker restante."
      return
    fi

    if [[ "${SECONDS}" -gt "${limite}" ]]; then
      echo "Timeout com ${restantes} broker(s) de pe. Seguindo mesmo assim." >&2
      return
    fi

    echo "${restantes} broker(s) restante(s)..."
    sleep 10
  done
}

desinstalar_operators() {
  titulo "Desinstalando os operators"

  if release_instalado spark-operator spark-operator; then
    helm uninstall spark-operator --namespace spark-operator --wait
  fi

  if release_instalado strimzi kafka; then
    helm uninstall strimzi --namespace kafka --wait
  fi
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
  remover_jobs_do_spark
  remover_clusters_do_kafka
  desinstalar_operators
  remover_aplicacoes
  remover_nodepools
  esperar_maquinas_encerrarem
else
  titulo "Cluster inacessivel, pulando a limpeza de dentro dele"
  cat <<'TEXTO'
A API do EKS nao respondeu. Sem essa etapa, brokers, jobs e webhooks nao sao
encerrados com ordem, e o terraform destroy pode travar ou deixar volumes soltos.

Se o cluster ainda existe, abra o tunel em outro terminal e rode de novo:

  ./infrastructure/tunnel.sh
  export HTTPS_PROXY=http://localhost:3128
TEXTO
  read -r -p "Seguir mesmo assim direto para o terraform destroy? [s/N] " seguir
  if [[ "${seguir}" != "s" ]]; then
    echo "Abortado."
    exit 1
  fi
fi

destruir_infraestrutura
listar_orfaos
