# shopping_amazon

Comandos a partir da raiz do repo.

## Local

```bash
uv run python process/src/airflow/run.py data_generator/main.py shopping_amazon_reviews
uv run python process/src/airflow/run.py data_eng/shopping_amazon/etl/main.py
```

## Cloud

```bash
kubectl exec -n airflow deploy/airflow-scheduler -- \
  airflow dags trigger shopping_amazon_reviews
```
