FROM apache/spark:4.2.0-python3

USER root

COPY etl_process /opt/spark/jobs/etl_process
COPY ml_process /opt/spark/jobs/ml_process
COPY datasets/shopping /opt/spark/datasets/shopping

RUN chown -R spark:spark /opt/spark/jobs /opt/spark/datasets

USER spark
