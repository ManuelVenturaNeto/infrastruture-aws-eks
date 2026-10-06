FROM apache/spark:4.2.0-python3

USER root

COPY process_etl /opt/spark/jobs/process_etl
COPY datasets/shopping/shopping /opt/spark/datasets/shopping

RUN chown -R spark:spark /opt/spark/jobs /opt/spark/datasets

USER spark
