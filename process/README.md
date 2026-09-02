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
      main.py                o codigo
      sparkapplication.yaml  como esse codigo roda no cluster
  ml_process/          treinos
  images/
    build.sh           constroi e envia a imagem para o ECR
    spark/Dockerfile   a imagem: Spark 4.2.0 + o seu codigo
```

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

O `Dockerfile` copia `etl_process/`, `ml_process/` e `datasets/shopping/` para
dentro da imagem. Se você criar outra área ou precisar de outro dataset, é uma
linha `COPY` a mais.

```bash
./process/src/images/build.sh spark 1.0.0
```

Ele faz login no ECR, constrói para `linux/amd64` (os NodePools só aceitam amd64)
e envia. No fim imprime o nome completo da imagem:

```
image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/kube-system-experiment/spark:1.0.0
```

A tag é **imutável** no ECR: subir `1.0.0` duas vezes falha, de propósito. Nova
versão de código, nova tag.

### 3. Escrever o manifesto

Copie o `sparkapplication.yaml` de um processo existente e ajuste quatro campos:

| Campo | O que colocar |
|---|---|
| `metadata.name` | Nome do job. Precisa ser único no namespace |
| `image` | O que o `build.sh` imprimiu. Troque `ACCOUNT_ID` pelo seu |
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
do `consolidateAfter` do NodePool (1 min no `spark`).

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

Uma armadilha que não aparece como erro: em job `type: Python` o Spark soma
**40%** de overhead de memória. `memory: 8g` vira um request de ~11,2Gi por pod,
e o Karpenter dimensiona a máquina por esse número.

## Gerar datasets

```bash
cd process
uv run python src/00-data-generator/generate.py shopping
uv run python src/00-data-generator/generate.py --help   # lista os disponiveis
```
