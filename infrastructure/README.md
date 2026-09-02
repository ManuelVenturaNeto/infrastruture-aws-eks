# infrastructure

Sobe e derruba o cluster EKS.

## Pré-requisitos

```bash
terraform -version
aws sts get-caller-identity       # credenciais validas
kubectl version --client
helm version
session-manager-plugin --version  # exigido pelo tunnel.sh
```

Se faltar algum:

```bash
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

curl -o /tmp/session-manager-plugin.deb \
  https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb
sudo dpkg -i /tmp/session-manager-plugin.deb
```

## Subir

A API do EKS não é pública (`endpoint_public_access = false`). O `kubectl` só a
alcança através do bastion, e o bastion só existe depois do `terraform apply`.
Por isso a **primeira** execução tem duas fases:

```bash
# fase 1 — cria VPC, EKS, ECR e o bastion. Para no passo do kubectl, de proposito.
./infrastructure/apply.sh
```

```bash
# terminal 2 — abre o tunel e fica aberto
./infrastructure/tunnel.sh
```

```bash
# terminal 1 — agora com o tunel de pe, roda de novo. O terraform nao recria nada.
export HTTPS_PROXY=http://localhost:3128
./infrastructure/apply.sh
```

Da segunda vez em diante, com o túnel já aberto, é um comando só.

### Escolhendo o que subir

```bash
./infrastructure/apply.sh                 # todos os NodePools
./infrastructure/apply.sh spark           # so o NodePool spark
./infrastructure/apply.sh spark kafka     # dois deles
./infrastructure/apply.sh --help          # lista os disponiveis
```

Ordem que o script garante: `terraform` → kubeconfig → Karpenter → StorageClass →
Spark Operator → Strimzi → NodePools escolhidos.

Passar `spark-gpu` instala junto o device plugin da NVIDIA, que é dependência dele.

**Nenhuma máquina de workload sobe aqui.** O Karpenter só cria EC2 quando existir
pod `Pending` que precise dela.

## Derrubar

```bash
./infrastructure/tunnel.sh                # em outro terminal, se nao estiver aberto
export HTTPS_PROXY=http://localhost:3128
./infrastructure/destroy.sh
```

Pede o nome do cluster como confirmação. Depois, em ordem: apaga os
`SparkApplication`, apaga os recursos do Strimzi e espera os brokers encerrarem,
desinstala os operators (o que remove os webhooks — se eles ficarem órfãos, o
destroy trava), apaga workloads e PVCs, apaga os NodePools, espera o Karpenter
encerrar as máquinas e só então roda o `terraform destroy`.

Se o cluster estiver inacessível ele avisa e pergunta antes de pular a limpeza
interna. Pular costuma deixar volume solto.

No fim lista o que **sobreviveu e continua sendo cobrado**: volumes EBS órfãos
(a StorageClass do Kafka é `Retain` de propósito) e snapshots. Nada disso é
apagado automaticamente:

```bash
aws ec2 delete-volume --region us-east-1 --volume-id vol-xxxxxxxx
```

As imagens no ECR **são** apagadas junto (`force_delete = true`), senão o destroy
falharia com os repositórios cheios.

## O que roda 24/7 e custa mesmo sem job nenhum

| Item | ~US$/mês |
|---|---|
| Control plane do EKS | 73 |
| Node group `system` (2× t3.medium) | 60 |
| NAT Gateway (1 só) | 33 + tráfego |
| Bastion (t3.micro) | 8 |
| **Piso** | **~175** |

Valores de tabela em `us-east-1`, para ordem de grandeza. Os NodePools em si
custam zero enquanto não houver pod esperando.

## Estrutura

```
infrastructure/
  apply.sh            sobe tudo, na ordem obrigatoria
  destroy.sh          derruba tudo, na ordem inversa
  tunnel.sh           abre o tunel SSM ate o proxy do bastion
  shared.tf           regiao e prefixo de nome
  cluster/            VPC, EKS, Karpenter IAM, ECR, bastion
  configs/
    karpenter/        instala o Karpenter
    storage/          StorageClass default
    gpu/              device plugin da NVIDIA
    operators/
      spark/          Spark Operator + namespaces spark-operator e spark-jobs
      kafka/          Strimzi + namespace kafka
    nodepools/        spark, spark-gpu, kafka, kafka-connect, kafka-streams
```
