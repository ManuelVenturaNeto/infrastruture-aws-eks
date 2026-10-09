# infrastructure

Sobe e derruba, com um comando cada, um cluster EKS (*Elastic Kubernetes Service*)
pronto para rodar os jobs Spark: Karpenter criando máquinas spot e GPU (*Graphics
Processing Unit*) sob demanda, lake de dados no S3 (*Simple Storage Service*) e os
serviços que você escolher.

## Em um minuto

```bash
./infrastructure/apply.sh spark            # base + Spark
./infrastructure/apply.sh airflow spark    # base + Airflow + Spark
./infrastructure/destroy.sh                # derruba tudo, menos o lake
```

| O que              | Detalhe                                      |
| ------------------ | -------------------------------------------- |
| Base               | EKS, rede, Karpenter, lake de dados e estado |
|                    | do Terraform                                 |
| Serviços opcionais | `airflow`, `spark`, `mlflow`, `kafka`        |
| Custo da base      | ~US$ 167/mês, com ou sem job rodando         |
| Custo dos serviços | somam por hora enquanto estão de pé          |
| Interfaces web     | `kubectl port-forward`, sem LoadBalancer     |

Os detalhes de cada parte estão abaixo.

## Pré-requisitos

```bash
aws login
terraform -version
aws sts get-caller-identity       # credenciais validas
kubectl version --client
helm version
```

Se faltar algum:

```bash
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

## Subir

```bash
./infrastructure/apply.sh
```

A API do EKS é pública (`endpoint_public_access = true`): o `kubectl` fala com
ela direto, e só entra quem tiver credencial IAM (*Identity and Access Management*)
desta conta.

### Escolhendo o que subir

```bash
./infrastructure/apply.sh                  # so a base, nenhuma aplicacao
./infrastructure/apply.sh airflow spark    # base + os dois servicos
./infrastructure/apply.sh --help           # lista os servicos disponiveis
```

**Sem argumento** sobe só a base: bucket de estado → `terraform` do cluster → lake
de dados → kubeconfig → Karpenter → StorageClass `gp3` → device plugin da NVIDIA.
Nenhuma máquina de workload sobe; o Karpenter só cria EC2 (*Elastic Compute Cloud*)
quando existir pod `Pending` que precise dela.

**Com argumento** sobe a base e, depois, cada serviço citado, **completo**. Se
qualquer passo de um serviço falhar, o script roda o `destroy.sh` daquele serviço
antes de sair: serviço pela metade não fica de pé.

O node group `system` é *tainted* com `CriticalAddonsOnly=true:NoSchedule`. Pod sem
`nodeSelector`/`tolerations` fica `Pending` de propósito, em vez de ocupar as `t3.medium`.

### Os serviços

O estado de cada serviço mora fora dos pods: banco em RDS (*Relational Database
Service*, o Postgres gerenciado da AWS), arquivos em S3 (*Simple Storage Service*) e
disco em volumes EBS (*Elastic Block Store*). O Kafka roda em KRaft (*Kafka Raft*), o
modo sem ZooKeeper.

| Serviço   | O que sobe                          | Estado fora do cluster     |
| --------- | ----------------------------------- | -------------------------- |
| `airflow` | Airflow 3 com `KubernetesExecutor`; | RDS Postgres + bucket S3   |
|           | DAGs via git-sync                   | dos logs das tasks         |
| `mlflow`  | MLflow com artefatos servidos pelo  | RDS Postgres + bucket S3   |
|           | servidor                            | dos artefatos              |
| `spark`   | Spark Operator, NodePools `spark` e | bucket S3 dos event logs   |
|           | `spark-gpu`, Spark History Server   |                            |
| `kafka`   | Strimzi, 3 brokers KRaft, kafka-ui, | volumes EBS dos brokers    |
|           | NodePools `kafka`, `kafka-connect`  |                            |
|           | e `kafka-streams`                   |                            |

Cada serviço é isolado dos outros em todas as camadas:

| Camada     | Como isola                                                      |
| ---------- | --------------------------------------------------------------- |
| Máquina    | NodePool próprio, com taint `workload=<serviço>`                |
| Kubernetes | namespaces com o label `service: <serviço>`                     |
| Rede       | NetworkPolicy: só entra tráfego de namespace do mesmo serviço   |
| Banco      | SG (*Security Group*) próprio nas máquinas; o RDS só aceita     |
|            | esse SG                                                         |
| AWS        | role de Pod Identity própria, com acesso só ao próprio bucket   |
| Terraform  | estado próprio na chave `services/<serviço>/` do bucket de      |
|            | estado                                                          |

O que continua compartilhado é a base: control plane, VPC (*Virtual Private Cloud*),
NAT (*Network Address Translation*), CoreDNS, Karpenter e o node group `system`.

O Terraform de cada serviço acha a base pelos nomes fixos (VPC, subnets, cluster) e
escreve direto no cluster os Secrets com a senha do RDS. Por isso ele usa o contexto
`kube-system-eks` do kubeconfig, que o `apply.sh` cria com `--alias`.

### Acessando as UIs

Tudo por `port-forward`. Nenhum serviço cria LoadBalancer.

```bash
kubectl port-forward -n airflow svc/airflow-api-server 8080:8080       # admin / admin
kubectl port-forward -n mlflow svc/mlflow 5000:80
kubectl port-forward -n spark-history svc/spark-history 18080:18080
kubectl port-forward -n kafka svc/kafka-ui 8081:80
```

O History Server lê `s3a://kube-system-spark/event-logs/`. Ele só mostra
um job se o job escrever ali (`spark.eventLog.enabled=true` e `spark.eventLog.dir`
apontando para esse caminho), com o `hadoop-aws` no classpath.

### Estado do Terraform

Todo estado mora no bucket `kube-system-tfstate`, com versionamento e
lock por arquivo (`use_lockfile`). O `state/apply.sh` cria o bucket na primeira vez
e não faz nada nas seguintes. Nenhum script apaga esse bucket.

| Camada    | Chave                                  |
| --------- | -------------------------------------- |
| `cluster` | `cluster/terraform.tfstate`            |
| `data`    | `data/terraform.tfstate`               |
| serviço   | `services/<serviço>/terraform.tfstate` |

### Lake de dados

O bucket `kube-system-lake` guarda os dados do pipeline, separados do
estado de qualquer serviço. Ele espelha `process/src/datasets/`: o caminho de um
dataset no lake é o mesmo de local, só com outro prefixo.

A role dos jobs Spark (service account `spark` em `spark-jobs`) lê e escreve no
lake. O lake sobrevive ao `destroy.sh` da raiz; só é apagado com `--include-lake`.

### DAGs do Airflow

O Airflow lê as DAGs por git-sync: um sidecar em cada pod puxa a pasta
`process/src/airflow` da branch `main` de
`github.com/ManuelVenturaNeto/infrastruture-aws-eks` a cada 30 s. Commit e push na
`main` basta; não há rebuild nem redeploy.

As tasks que disparam jobs Spark usam o `SparkKubernetesOperator`, que cria um
`SparkApplication` no namespace `spark-jobs` e acompanha o driver até o fim. O
serviço `spark` dá essa permissão ao service account `airflow-worker` pelo
`airflow-rbac.yaml`:

| Recurso             | Verbos                                       |
| ------------------- | -------------------------------------------- |
| `sparkapplications` | create, get, list, watch, patch, delete      |
| `pods`, `pods/log`  | get, list, watch                             |

A permissão fica no serviço `spark` porque o namespace é dele: ela nasce e some com
o `spark-jobs`, e o `airflow` não depende do `spark` estar de pé para subir.

### Adicionando um serviço

Uma pasta nova em `services/`, com `apply.sh` e `destroy.sh` executáveis. O
`apply.sh` e o `destroy.sh` da raiz descobrem a pasta sozinhos. O `destroy.sh` do
serviço precisa rodar sem erro mesmo quando o serviço nunca subiu.

Se o serviço precisa de bucket, ele usa o módulo `modules/service-storage`: bucket,
role com leitura e escrita nele e a associação de Pod Identity com os service
accounts do serviço. O backend do Terraform aponta para a chave
`services/<serviço>/terraform.tfstate`.

## Derrubar

```bash
./infrastructure/destroy.sh                  # tudo, menos o lake
./infrastructure/destroy.sh --include-lake   # tudo, inclusive o lake
```

Não pede confirmação. **Tudo é apagado, menos o lake de dados e o bucket de
estado.** Em ordem:

1. Roda o `destroy.sh` de todos os serviços, tenham subido ou não. Cada um apaga o
   que encontrar: releases do Helm, CRs (*Custom Resources*), NodePools (e espera as máquinas saírem),
   o próprio Terraform (RDS, bucket com o conteúdo, roles, SGs) e os namespaces.
2. Apaga o que sobrar em qualquer namespace, os NodePools restantes, e espera o
   Karpenter encerrar as máquinas.
3. Roda o `terraform destroy` da base.
4. Com `--include-lake`, roda o `terraform destroy` do lake, que apaga o bucket com
   todo o conteúdo. Sem a flag, só avisa que o lake continua.
5. Apaga os volumes EBS e snapshots com a tag `kubernetes.io/cluster/kube-system-eks`,
   que o driver EBS põe em tudo o que cria.

No fim lista volumes soltos e snapshots que ainda existirem na conta. O que aparecer
ali não tem a tag do cluster e não foi apagado.

As imagens no ECR (*Elastic Container Registry*) **são** apagadas junto (`force_delete = true`), senão o destroy
falharia com os repositórios cheios.

Se o cluster estiver inacessível, ele avisa e pula a limpeza interna. O Terraform
dos serviços ainda roda (RDS e buckets somem), mas esquece os Secrets em vez de
apagá-los no cluster. Máquinas do Karpenter que sobrarem podem travar o
`terraform destroy` da base.

## Quanto custa

A base roda 24/7 e custa mesmo sem serviço nenhum:

| Item                               | ~US$/mês     |
| ---------------------------------- | ------------ |
| Control plane do EKS               | 73           |
| Node group `system` (2× t3.medium) | 60           |
| NAT Gateway (1 só)                 | 33 + tráfego |
| **Piso**                           | **~167**     |

Cada serviço soma enquanto estiver de pé:

| Serviço   | O que custa                                      | ~US$/hora |
| --------- | ------------------------------------------------ | --------- |
| `airflow` | 1 máquina on-demand de 2–4 vCPU + RDS t4g.micro  | 0,12–0,21 |
| `mlflow`  | 1 máquina on-demand de 2 vCPU + RDS t4g.micro    | 0,12      |
| `spark`   | 1 máquina spot para o History Server, mais os    | 0,03 +    |
|           | jobs                                             | jobs      |
| `kafka`   | 1 máquina on-demand de 4–8 vCPU + 3 volumes gp3  | 0,20–0,40 |

Valores de tabela em `us-east-1`, para ordem de grandeza. Criar ou destruir um RDS
leva de 5 a 10 minutos.

## Estrutura

```
infrastructure/
  apply.sh              base; com argumento, + os servicos citados
  destroy.sh            servicos, base e orfaos; --include-lake apaga o lake
  shared.tf             regiao e prefixo de nome
  state/                cria o bucket do estado do Terraform
  cluster/              VPC, EKS, Karpenter IAM, ECR
  data/                 lake de dados; fora do destroy padrao
  modules/
    service-storage/    bucket + role + Pod Identity de um servico
  configs/
    karpenter/          instala o Karpenter
    storage/            StorageClass default
    gpu/                device plugin da NVIDIA
  services/
    airflow/
      apply.sh
      destroy.sh
      namespaces.yaml
      networkpolicy.yaml
      nodepools/        NodeClass com o SG do servico + NodePool
      terraform/        bucket, RDS, SGs, Pod Identity, Secrets
      helm-values.yaml
    mlflow/             mesmo formato do airflow
    spark/
      apply.sh
      destroy.sh
      namespaces.yaml
      networkpolicy.yaml
      airflow-rbac.yaml permite ao Airflow criar SparkApplications
      nodepools/        spark, spark-gpu
      terraform/        bucket dos event logs, acesso ao lake, Pod Identity
      operator/         Spark Operator
      history-server/   Spark History Server
    kafka/
      apply.sh
      destroy.sh
      namespaces.yaml
      networkpolicy.yaml
      nodepools/        kafka, kafka-connect, kafka-streams
      operator/         Strimzi
      brokers/          CR Kafka + KafkaNodePool
      ui/               kafka-ui
```
