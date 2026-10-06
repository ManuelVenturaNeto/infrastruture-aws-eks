FROM apache/spark:4.2.0-python3

USER root

RUN pip3 install --no-cache-dir \
      "numpy==2.2.6" \
      "pandas==2.3.3" \
      "pyarrow==22.0.0" \
      "xgboost-cpu==3.2.0"

COPY process_ml /opt/spark/jobs/process_ml
COPY datasets/shopping/shopping /opt/spark/datasets/shopping

RUN chown -R spark:spark /opt/spark/jobs /opt/spark/datasets

USER spark
