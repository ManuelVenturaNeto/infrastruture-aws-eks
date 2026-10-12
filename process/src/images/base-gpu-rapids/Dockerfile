FROM apache/spark:4.2.0-python3

ARG MAVEN=https://repo1.maven.org/maven2
ARG DELTA_ARTIFACT=delta-spark_4.2_2.13
ARG DELTA_VERSION=4.4.0
ARG HADOOP_VERSION=3.5.0
ARG AWS_SDK_VERSION=2.35.4
ARG RAPIDS_VERSION=26.08.1

USER root

RUN cd /opt/spark/jars \
 && curl -fsSLO "${MAVEN}/io/delta/${DELTA_ARTIFACT}/${DELTA_VERSION}/${DELTA_ARTIFACT}-${DELTA_VERSION}.jar" \
 && curl -fsSLO "${MAVEN}/io/delta/delta-storage/${DELTA_VERSION}/delta-storage-${DELTA_VERSION}.jar" \
 && curl -fsSLO "${MAVEN}/org/apache/hadoop/hadoop-aws/${HADOOP_VERSION}/hadoop-aws-${HADOOP_VERSION}.jar" \
 && curl -fsSLO "${MAVEN}/software/amazon/awssdk/bundle/${AWS_SDK_VERSION}/bundle-${AWS_SDK_VERSION}.jar" \
 && curl -fsSLO "${MAVEN}/com/nvidia/rapids-4-spark_2.13/${RAPIDS_VERSION}/rapids-4-spark_2.13-${RAPIDS_VERSION}-cuda12.jar"

RUN pip3 install --no-cache-dir --no-deps "delta-spark==${DELTA_VERSION}"

USER spark
