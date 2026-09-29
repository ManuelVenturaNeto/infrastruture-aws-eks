# project-pipeline-distribuited-spark-EKS

Processos Spark rodando no EKS (*Elastic Kubernetes Service*). Todos os comandos
rodam da raiz do repositório. Para subir o cluster, veja
[infrastructure/README.md](infrastructure/README.md).

## Rodar

### 1. Gerar os dados

```bash
uv run python process/src/data_generator/generate.py shopping
uv run python process/src/data_generator/generate.py --help
```

### 2. Testar local

```bash
uv run python process/src/process_etl/spark_pipe_shopping/main.py \
  --input process/src/datasets/shopping
```

Roda em `local[*]`, sem cluster. Pega erro de sintaxe e de schema antes de gastar
EC2 (*Elastic Compute Cloud*).

### 3. Construir e subir a imagem

```bash
REGISTRY=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com
IMAGE=${REGISTRY}/kube-system-experiment/spark:1.0.0

aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin "${REGISTRY}"

docker build --platform linux/amd64 \
  --file process/src/process_etl/spark_pipe_shopping/images/cpu/Dockerfile \
  --tag "${IMAGE}" process/src

docker push "${IMAGE}"
```

- `--platform linux/amd64` é obrigatório: imagem ARM sobe sem erro e só falha no
  cluster, com `exec format error`.
- O contexto é `process/src` (último argumento): os `COPY` do Dockerfile são
  relativos a ele.
- A tag é imutável no ECR (*Elastic Container Registry*): código novo, tag nova.

### 4. Disparar

No `sparkapplication.yaml`, troque `ACCOUNT_ID` pela sua conta e confira `image`,
`mainApplicationFile` (caminho dentro da imagem) e `arguments`.

```bash
kubectl apply -f process/src/process_etl/spark_pipe_shopping/sparkapplication.yaml
```

### 5. Acompanhar

```bash
kubectl get sparkapplication -n spark-jobs -w
kubectl get pods -n spark-jobs -o wide
kubectl logs -n spark-jobs <nome-do-job>-driver -f
```

Pod `Pending` por 1 a 3 minutos é a EC2 subindo.

### 6. Rodar de novo ou limpar

Aplicar o mesmo nome outra vez não faz nada. Apague antes:

```bash
kubectl delete sparkapplication <nome> -n spark-jobs
```

O Karpenter encerra as máquinas vazias depois de 5 minutos.

## GPU

Há duas imagens de GPU (*Graphics Processing Unit*), e elas não se substituem:

| Manifesto                      | Imagem         | O que acelera              |
| ------------------------------ | -------------- | -------------------------- |
| `sparkapplication-rapids.yaml` | `spark-rapids` | Spark SQL inteiro, sem     |
|                                | (Spark 3.5.9)  | mudar código               |
| `sparkapplication-gpu.yaml`    | `spark-gpu`    | só o XGBoost, com          |
|                                | (Spark 4.2.0)  | `device="cuda"`            |

O RAPIDS não tem suporte a Spark 4, por isso a imagem dele fica no 3.5.9.

Mandar a imagem de CPU (*Central Processing Unit*) para o NodePool `spark-gpu` não
dá erro: roda em CPU e a GPU fica parada, custando. Para confirmar que a GPU está
em uso:

```bash
kubectl logs -n spark-jobs <job>-exec-1 | grep -i "rapids\|cuda\|gpu"
```

## Quando algo dá errado

```bash
kubectl describe pod -n spark-jobs <pod>
```

| Sintoma                         | Causa provável                            |
| ------------------------------- | ----------------------------------------- |
| `untolerated taint`             | Falta a toleration no manifesto           |
| `Pending` por mais de 5 min     | Limite de CPU do NodePool ou sem spot     |
| `pods is forbidden`             | `serviceAccount` diferente de `spark`     |
| `ImagePullBackOff`              | Tag inexistente no ECR                    |
| `python: can't open file`       | `mainApplicationFile` fora da imagem      |
| `OOMKilled` (*Out Of Memory*)   | Aumente `memory` do executor              |

Em job `type: Python` o Spark soma 40% de memória: `memory: 8g` vira ~11,2Gi por
pod, e é por esse número que o Karpenter escolhe a máquina.

## Airflow

As DAGs ficam em `process/src/airflow/`. Commit e push na `main` e o git-sync
entrega ao Airflow em até 30 s.
