FROM ghcr.io/apache/flink-kubernetes-operator:1.12.1

# Ensure the lib directory exists
ARG LIB_DIR=${FLINK_HOME}/lib
RUN mkdir -p ${LIB_DIR}

# Copy Flink Doris Connector jar from it's docker image
COPY --from=ghcr.io/thealtoclef/doris-flink-connector:latest /flink-doris-connector.jar ${LIB_DIR}/flink-doris-connector.jar
