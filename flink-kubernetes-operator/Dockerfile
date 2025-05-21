FROM ghcr.io/apache/flink-kubernetes-operator:1.11.0

# Ensure the lib directory exists
ARG LIB_DIR=${FLINK_HOME}/lib
RUN mkdir -p ${LIB_DIR}

# Copy local jars to the lib directory
COPY lib/* ${LIB_DIR}/
