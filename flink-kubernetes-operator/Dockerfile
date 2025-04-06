FROM ghcr.io/apache/flink-kubernetes-operator:1.11.0

ARG FLINK_VERSION=1.20
ARG FLINK_DORIS_CONNECTOR_VERSION=25.0.0

# Ensure the lib directory exists
RUN mkdir -p ${FLINK_HOME}/lib

# Download flink-doris-connector jar
RUN wget -O ${FLINK_HOME}/lib/flink-doris-connector.jar \
    https://repository.apache.org/content/repositories/releases/org/apache/doris/flink-doris-connector-${FLINK_VERSION}/${FLINK_DORIS_CONNECTOR_VERSION}/flink-doris-connector-${FLINK_VERSION}-${FLINK_DORIS_CONNECTOR_VERSION}.jar
