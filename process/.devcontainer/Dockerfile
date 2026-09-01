FROM python:3.13-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        procps \
        openjdk-17-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

RUN JAVA_DIR="$(dirname "$(dirname "$(readlink -f "$(command -v javac)")")")" \
    && ln -sfn "$JAVA_DIR" /usr/lib/jvm/default-java
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

RUN pip install --no-cache-dir \
        pyspark==4.0.1 \
        delta-spark==4.0.1 \
        ipykernel \
        jupyterlab \
        scikit-learn \
        pandas \
        pyarrow \
        matplotlib \
        seaborn \
        mlflow

WORKDIR /workspace

# Dev Containers: Reopen in Container