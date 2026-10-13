# data_generator

Baixa cada dataset em parquet para `<out>/<nome>/<nome>`. Rodar da raiz do
repositório:

```bash
uv run python process/src/airflow/run.py data_generator/main.py <dataset>
uv run python process/src/airflow/run.py data_generator/main.py <dataset> \
  --out s3://kube-system-lake
```

Sem `--out`, grava em `process/src/datasets`. Com um bucket, cada arquivo sobe
assim que termina e sai do disco, usando a conta do `aws login`; arquivo que já
está no bucket é pulado, então rodar de novo continua de onde parou.

No cluster, a DAG `data_generator` roda só por disparo manual. O parâmetro
`dataset` escolhe um processo ou `all`, e cada processo sobe como uma
SparkApplication própria, gravando direto no lake:

```bash
kubectl exec -n airflow deploy/airflow-scheduler -- \
  airflow dags trigger data_generator --conf '{"dataset": "stocks_b3"}'
```

| Dataset                          | Tamanho  | O que é                        |
| -------------------------------- | -------- | ------------------------------ |
| `hotels`                         | ~1 MB    | reservas de hotel              |
| `credit`                         | ~3 MB    | inadimplência de crédito       |
| `insurance`                      | ~13 MB   | acionamento de seguro de carro |
| `shopping`                       | ~16 MB   | pedidos do Olist               |
| `cards`                          | ~70 MB   | fraude em cartão               |
| `stocks_b3`                      | ~540 MB  | cotações da bolsa desde 1986   |
| `real_estate`                    | ~1,7 GB  | empréstimos da Fannie Mae      |
| `movies_imdb`                    | ~1,9 GB  | base pública de filmes         |
| `movies_amazon`                  | ~2,1 GB  | avaliações de filmes da Amazon |
| `shopping_amazon_meta`           | ~5,4 GB  | catálogo de produtos Amazon    |
| `insurance_health_beneficiaries` | ~13 GB   | planos de saúde: beneficiários |
| `shopping_amazon_reviews`        | ~18,1 GB | avaliações de produtos Amazon  |
| `insurance_medicare_partd`       | ~22 GB   | medicamentos do Medicare       |
| `insurance_health_claims`        | ~35 GB   | planos de saúde: atendimentos  |

Para começar, use um dos pequenos. O `stocks_b3` aceita `--start_year` e
`--end_year` para baixar só alguns anos. O detalhe de cada dataset vem abaixo.

Cada dataset é uma pasta em `extraction/` com uma função `ingest` e um
`machine.py`, que define o `Cpu` do driver no cluster; o nome da pasta é o
nome no comando e na DAG. O que mais de um processo usa fica em `utils/`:
`network/` (download), `formats/` (parquet), `storage/` (local ou S3) e
`sources/` (listas de URLs e ANS).

## shopping

```bash
uv run python process/src/airflow/run.py data_generator/main.py shopping
```

Pedidos do Olist (e-commerce brasileiro) já cruzados com cliente, vendedor,
produto e avaliação. 1 arquivo, ~16 MB.

## shopping_amazon_reviews

```bash
uv run python process/src/airflow/run.py data_generator/main.py \
  shopping_amazon_reviews
```

Avaliações do Amazon Reviews 2023: `user_id`, `parent_asin` (ASIN, *Amazon
Standard Identification Number*), `rating`, `timestamp`, `title`, `text`,
`helpful_vote` e `verified_purchase`. Os 26 primeiros arquivos cobrem Toys,
Cell Phones, Musical Instruments, Electronics e Arts, categorias que têm
metadados em `shopping_amazon_meta`. 26 arquivos, ~99 milhões de linhas,
~18,1 GB.

## shopping_amazon_meta

```bash
uv run python process/src/airflow/run.py data_generator/main.py \
  shopping_amazon_meta
```

Catálogo de produtos do Amazon Reviews 2023 (título, loja, preço, categorias,
`average_rating`, `rating_number`, `bought_together`) de 9 categorias. Junta
com `shopping_amazon_reviews` por `parent_asin`. 33 arquivos, ~5,5 milhões de
produtos, ~5,4 GB.

Os dois datasets da Amazon juntos somam ~23,5 GB.

## credit

```bash
uv run python process/src/airflow/run.py data_generator/main.py credit
```

Give Me Some Credit, do OpenML: inadimplência de crédito pessoal em até dois
anos. 1 arquivo, ~3 MB.

## insurance

```bash
uv run python process/src/airflow/run.py data_generator/main.py insurance
```

Porto Seguro Safe Driver Prediction, do OpenML: se o motorista vai acionar o
seguro no ano seguinte. 1 arquivo, ~13 MB.

## insurance_health_claims

```bash
uv run python process/src/airflow/run.py data_generator/main.py \
  insurance_health_claims
```

Atendimentos pagos pelos planos de saúde, do TISS (*Troca de Informações na
Saúde Suplementar*) da ANS (*Agência Nacional de Saúde Suplementar*), por
estado e mês. Cada atendimento (`*_events`: faixa etária, sexo, plano,
município, caráter e, nas internações, CID — *Classificação Internacional de
Doenças*) liga aos seus itens (`*_items`: procedimento, quantidade, valor
informado e pago) por `ID_EVENTO_ATENCAO_SAUDE`. Uma pasta por tabela:
`outpatient_events` e `outpatient_items` (ambulatorial, 2024–2025),
`hospital_events` e `hospital_items` (internações, 2015–2025). 8424 arquivos,
~5 bilhões de linhas, ~35 GB.

## insurance_health_beneficiaries

```bash
uv run python process/src/airflow/run.py data_generator/main.py \
  insurance_health_beneficiaries
```

Beneficiários de planos de saúde da ANS, consolidados por operadora,
município, sexo, faixa etária, plano e tipo de contratação, com ativos,
aderidos e cancelados no mês. De 05/2021 a 08/2026, um arquivo por estado e
mês. 1728 arquivos, ~1 bilhão de linhas, ~13 GB.

## insurance_medicare_partd

```bash
uv run python process/src/airflow/run.py data_generator/main.py \
  insurance_medicare_partd
```

Planos de medicamentos do Medicare Part D, dos arquivos trimestrais do CMS
(*Centers for Medicare & Medicaid Services*), de 2023T4 a 2026T3. Uma pasta
por tabela: `pharmacy_networks` (farmácias da rede de cada plano e taxas de
dispensação), `pricing` (custo unitário por plano e NDC — *National Drug
Code*), `basic_drugs_formulary`, `beneficiary_cost`, `plan_information`,
`geographic_locator` e as demais. Planos ligam por `CONTRACT_ID`, `PLAN_ID` e
`SEGMENT_ID`. 11 trimestres, ~4 bilhões de linhas, ~22 GB.

## cards

```bash
uv run python process/src/airflow/run.py data_generator/main.py cards
```

Credit Card Fraud Detection, do OpenML: transações de cartão rotuladas como
fraude ou não. 1 arquivo, ~70 MB.

## real_estate

```bash
uv run python process/src/airflow/run.py data_generator/main.py real_estate
uv run python process/src/airflow/run.py data_generator/main.py \
  real_estate --files 6765
```

Desempenho mensal de empréstimos imobiliários da Fannie Mae. O padrão baixa 400
de 6765 arquivos (~1,7 GB); com `--files 6765` vem tudo, ~3,2 bilhões de
linhas, ~29,4 GB.

## hotels

```bash
uv run python process/src/airflow/run.py data_generator/main.py hotels
```

Reservas de dois hotéis portugueses, com cancelamento. 1 arquivo, ~1 MB.

## movies_imdb

```bash
uv run python process/src/airflow/run.py data_generator/main.py movies_imdb
```

As 7 tabelas públicas do IMDb (*Internet Movie Database*): títulos, nomes
alternativos, equipe, episódios, elenco, notas e pessoas. Chegam em TSV
(*Tab-Separated Values*) e são convertidas para parquet. ~1,9 GB.

## movies_amazon

```bash
uv run python process/src/airflow/run.py data_generator/main.py movies_amazon
```

Avaliações de filmes e séries da Amazon já unidas aos metadados do produto.
33 arquivos, ~6,7 milhões de linhas, ~2,1 GB.

## stocks_b3

```bash
uv run python process/src/airflow/run.py data_generator/main.py stocks_b3
uv run python process/src/airflow/run.py data_generator/main.py stocks_b3 \
  --start_year 2020 --end_year 2024
```

Cotações diárias da B3 (*Brasil, Bolsa, Balcão*) a partir do COTAHIST, um
arquivo por ano desde 1986. Gera também `stocks_b3_events` com
desdobramentos, grupamentos e bonificações das empresas listadas. Todos os
anos, ~540 MB.
