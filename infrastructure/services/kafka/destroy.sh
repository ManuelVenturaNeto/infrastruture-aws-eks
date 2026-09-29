#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TIMEOUT_BROKERS=900

cluster_acessivel() {
  kubectl cluster-info >/dev/null 2>&1
}

crd_instalado() {
  kubectl get crd "$1" >/dev/null 2>&1
}

release_instalado() {
  helm status "$1" --namespace "$2" >/dev/null 2>&1
}

pods_do_kafka() {
  kubectl get pods -n kafka -l strimzi.io/kind=Kafka --no-headers 2>/dev/null | wc -l | tr -d ' '
}

esperar_brokers_encerrarem() {
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

remover_clusters_do_kafka() {
  if ! crd_instalado kafkas.kafka.strimzi.io; then
    return
  fi

  kubectl delete kafkaconnect --all -A --ignore-not-found
  kubectl delete kafkatopic --all -A --ignore-not-found
  kubectl delete kafkauser --all -A --ignore-not-found
  kubectl delete kafka --all -A --ignore-not-found
  kubectl delete kafkanodepool --all -A --ignore-not-found

  esperar_brokers_encerrarem
}

if ! cluster_acessivel; then
  exit 0
fi

if release_instalado kafka-ui kafka; then
  helm uninstall kafka-ui --namespace kafka --wait
fi

remover_clusters_do_kafka

if release_instalado strimzi kafka; then
  helm uninstall strimzi --namespace kafka --wait
fi

kubectl delete -f "${HERE}/namespaces.yaml" --ignore-not-found --wait --timeout=10m
kubectl delete -R -f "${HERE}/nodepools/" --ignore-not-found --wait --timeout=30m
