FROM apache/spark:3.5.9-python3

ARG RAPIDS_VERSION=26.08.1
ARG RAPIDS_JAR=rapids-4-spark_2.12-${RAPIDS_VERSION}-cuda12.jar

USER root

RUN curl -fsSL -o "/opt/spark/jars/${RAPIDS_JAR}" \
      "https://repo1.maven.org/maven2/com/nvidia/rapids-4-spark_2.12/${RAPIDS_VERSION}/${RAPIDS_JAR}" \
 && chmod 644 "/opt/spark/jars/${RAPIDS_JAR}"

USER spark
