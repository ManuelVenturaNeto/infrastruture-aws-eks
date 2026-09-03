FROM apache/spark:4.2.0-python3

USER root

RUN pip3 install --no-cache-dir \
      "numpy==2.2.6" \
      "pandas==2.3.3" \
      "pyarrow==22.0.0"

USER spark
