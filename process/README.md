# process

O código que roda no cluster. Este README assume a infraestrutura **já de pé** —
para subir, veja [infrastructure/README.md](../infrastructure/README.md).

## Estrutura

```
process/src/
  00-data-generator/   baixa datasets publicos para src/datasets/
  datasets/            os dados
  etl_process/         processos Spark
    01_spark_pipe_shopping/
      main.py                      o codigo
      sparkapplication.yaml        como esse codigo roda no cluster
      sparkapplication-rapids.yaml a variante em GPU
      images/spark/Dockerfile      Spark 4.2.0 + o seu codigo       (CPU)
  ml_process/          treinos
    01_xgboost/
      train.py                     XGBoost distribuido, com device=cuda
      sparkapplication.yaml
      images/spark-gpu/Dockerfile     Spark 4.2.0 + XGBoost/CUDA    (GPU, ML)
      images/spark-rapids/Dockerfile  Spark 3.5.9 + RAPIDS          (GPU, SQL)
```

Cada processo carrega o seu `images/`. Nada é compartilhado entre processos: mudar
a imagem de um não pode quebrar o outro.

Cada processo é uma pasta com **duas** coisas: o `main.py` e o
`sparkapplication.yaml` que o executa. Eles andam juntos — o YAML aponta para o
caminho do script dentro da imagem e passa os argumentos que o `argparse` espera.

## Rodar um processo

### 1. Escrever o código

```
process/src/etl_process/<nn>_<nome>/main.py
```

Use `argparse` para tudo que muda entre execuções (caminhos, datas, filtros).
Esses valores viram `arguments:` no YAML, e é o que permite reaproveitar a mesma
imagem em rodadas diferentes.

Testar local, sem cluster:

```bash
cd process
uv run python src/etl_process/01_spark_pipe_shopping/main.py --input src/datasets/shopping
```

Roda em modo `local[*]`, num processo só. Serve para pegar erro de sintaxe e de
schema antes de gastar EC2.

### 2. Construir a imagem

O `Dockerfile` copia `etl_process/`, `ml_process/` e `datasets/` para dentro da
imagem. Se você criar outra área ou precisar de outro dataset, é uma linha `COPY`
a mais.

```bash
cd process/src

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGISTRY=${ACCOUNT}.dkr.ecr.us-east-1.amazonaws.com
IMAGE=${REGISTRY}/kube-system-experiment/spark:1.0.0

aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin "${REGISTRY}"

docker build --platform linux/amd64 \
  --file etl_process/01_spark_pipe_shopping/images/spark/Dockerfile \
  --tag "${IMAGE}" .

docker push "${IMAGE}"
```

Duas coisas nesses comandos não são detalhe:

O `--platform linux/amd64` é obrigatório. Todos os NodePools exigem `kubernetes.io/arch:
amd64`; uma imagem construída num Mac ARM sobe para o ECR sem reclamar e falha só no
cluster, com `exec format error`.

O `--file` aponta fundo na árvore, mas o **contexto continua sendo `process/src`** — é o
`.` no fim. Os `COPY` do Dockerfile são relativos ao contexto, não ao Dockerfile. Rodar
`docker build` de dentro da pasta `images/` falha com `COPY etl_process: not found`.

A tag é **imutável** no ECR: subir `1.0.0` duas vezes falha, de propósito. Nova
versão de código, nova tag.

### 3. Escrever o manifesto

Copie o `sparkapplication.yaml` de um processo existente e ajuste quatro campos:

| Campo | O que colocar |
|---|---|
| `metadata.name` | Nome do job. Precisa ser único no namespace |
| `image` | O `${IMAGE}` que você acabou de subir. Troque `ACCOUNT_ID` pelo seu |
| `mainApplicationFile` | `local:///opt/spark/jobs/<area>/<pasta>/main.py` |
| `arguments` | Os flags do seu `argparse` |

`local://` significa "dentro da imagem", não a sua máquina.

Não mexa nos blocos `nodeSelector` e `tolerations`: eles são o que faz o pod
cair no NodePool certo. Sem a toleration o pod fica `Pending` para sempre e
nenhuma máquina é criada.

### 4. Disparar

```bash
export HTTPS_PROXY=http://localhost:3128    # com o tunnel.sh aberto

kubectl apply -f process/src/etl_process/01_spark_pipe_shopping/sparkapplication.yaml
```

### 5. Acompanhar

```bash
# o estado do job: SUBMITTED -> RUNNING -> COMPLETED
kubectl get sparkapplication -n spark-jobs -w

# os pods. Ficam Pending por 1-3 minutos: e a EC2 subindo. E normal.
kubectl get pods -n spark-jobs -o wide

# o Karpenter criando a maquina
kubectl get nodeclaims

# a saida do job
kubectl logs -n spark-jobs <nome-do-job>-driver -f
```

### 6. Rodar de novo

Um `SparkApplication` é de execução única. Aplicar o mesmo nome outra vez **não
faz nada**:

```bash
kubectl delete sparkapplication <nome> -n spark-jobs
kubectl apply -f .../sparkapplication.yaml
```

Para execução recorrente existe o `ScheduledSparkApplication`, com um campo
`schedule` em formato cron.

### 7. Limpar

```bash
kubectl delete sparkapplication <nome> -n spark-jobs
```

Os pods somem, os nodes ficam vazios e o Karpenter encerra as EC2 sozinho depois
do `consolidateAfter` do NodePool (5 min no `spark`).

## Rodar na GPU

Existem **duas** imagens de GPU, e elas não são intercambiáveis. A diferença não é
preferência, é uma restrição de terceiro:

| | `spark-rapids` | `spark-gpu` |
|---|---|---|
| Spark | 3.5.9 | 4.2.0 |
| O que a GPU acelera | o **Spark SQL inteiro**, sem mudar o código | só o que o **seu Python** mandar para ela |
| Como | plugin RAPIDS (`com.nvidia.spark.SQLPlugin`) | XGBoost com `device="cuda"` |
| Precisa reescrever o job? | Não | Sim, é código de ML |
| Exemplo | `etl_process/.../sparkapplication-rapids.yaml` | `ml_process/01_xgboost/sparkapplication.yaml` |

**Por que o RAPIDS não roda no 4.2.0:** o jar do RAPIDS carrega um *shim* por versão
de Spark, e a 26.08.1 só traz de `spark330` a `spark359`. Não existe `spark4xx`. Para
conferir numa versão nova do RAPIDS, sem baixar 1 GB:

```bash
python3 -c "
import re,urllib.request
u='https://repo1.maven.org/maven2/com/nvidia/rapids-4-spark_2.12/maven-metadata.xml'
print(re.findall(r'<latest>([^<]+)</latest>', urllib.request.urlopen(u).read().decode()))
"
```

Se um dia aparecer shim de Spark 4, as duas imagens viram uma só.

**Por que o `spark-gpu` usa XGBoost 3.2.0** e não a 3.4.1 do `pyproject.toml`: a imagem
oficial `apache/spark:4.2.0-python3` traz Python 3.10, e o XGBoost exige Python 3.12 a
partir da 3.3.0. A 3.2.0 é a última que roda em 3.10 — e tem CUDA e NCCL compilados,
que é o que importa. Seu ambiente local, em Python 3.12, continua na 3.4.1.

### Construir e disparar

Mesmo procedimento da seção 2, trocando `--file` e o nome no `--tag`:

```bash
cd process/src

docker build --platform linux/amd64 \
  --file ml_process/01_xgboost/images/spark-rapids/Dockerfile \
  --tag "${REGISTRY}/kube-system-experiment/spark-rapids:1.0.0" .

docker build --platform linux/amd64 \
  --file ml_process/01_xgboost/images/spark-gpu/Dockerfile \
  --tag "${REGISTRY}/kube-system-experiment/spark-gpu:1.0.0" .
```

O contexto é `process/src` nos dois, pelo mesmo motivo. Os repositórios ECR dos três
nomes são criados pelo Terraform (`image_repositories`).

```bash
kubectl apply -f process/src/ml_process/01_xgboost/sparkapplication.yaml
```

O driver vai para o NodePool `spark` (CPU, on-demand) e só os executores vão para o
`spark-gpu`. Driver não usa GPU: deixá-lo numa máquina de GPU é jogar fora a parte cara.

### Uma diferença sutil de configuração

```yaml
"spark.task.resource.gpu.amount": "0.5"   # spark-rapids: varias tasks dividem a GPU
"spark.task.resource.gpu.amount": "1"     # spark-gpu:    XGBoost quer 1 task por GPU
```

O RAPIDS paraleliza dentro da placa e quer `1 / executor.cores`. O XGBoost exige uma
task por GPU e trava se houver mais.

### O modo de falhar que não dá erro

Se você mandar um job para o NodePool `spark-gpu` usando a imagem `spark` (a de CPU),
tudo **funciona**: o pod sobe, a máquina de ~US$1/h fica de pé, o Spark processa em CPU
e a GPU nunca é tocada. Não há mensagem de erro — o único sintoma é a fatura. Para
confirmar que a GPU está de fato em uso, procure no log do executor:

```bash
kubectl logs -n spark-jobs <job>-exec-1 | grep -i "rapids\|cuda\|gpu"
```

No `spark-rapids` a linha `RAPIDS Accelerator is enabled` tem que aparecer.

## Quando algo dá errado

```bash
kubectl describe pod -n spark-jobs <pod>     # a secao Events, no fim, diz o motivo
kubectl describe sparkapplication -n spark-jobs <nome>
```

| Sintoma | Causa provável |
|---|---|
| `untolerated taint {workload: spark}` | Falta a toleration no manifesto |
| `Pending` por mais de 5 min | `limits.cpu` do NodePool estourado, ou sem capacidade spot |
| `SUBMISSION_FAILED` com `pods is forbidden` | `serviceAccount` errado — tem que ser `spark` |
| `ImagePullBackOff` | Tag inexistente, ou nó sem permissão no ECR |
| `python: can't open file` | `mainApplicationFile` aponta para caminho que não existe na imagem |
| `OOMKilled` | Aumente `memory` do executor |
| `cudaErrorInsufficientDriver` | Driver da AMI mais velho que o runtime CUDA da imagem |
| `Unsupported Spark version` no shim | RAPIDS sem shim para o `sparkVersion` do manifesto |

Uma armadilha que não aparece como erro: em job `type: Python` o Spark soma
**40%** de overhead de memória. `memory: 8g` vira um request de ~11,2Gi por pod,
e o Karpenter dimensiona a máquina por esse número.

## Gerar datasets

```bash
cd process
uv run python src/00-data-generator/generate.py shopping
uv run python src/00-data-generator/generate.py --help   # lista os disponiveis
```
