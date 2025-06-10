# Build stage
FROM maven:3-eclipse-temurin-8 AS builder

# Clone and build the Flink Doris Connector (option 6 is Flink version 1.20.x)
WORKDIR /workspace
RUN git clone https://github.com/thealtoclef/doris-flink-connector.git --branch master --depth 1
WORKDIR /workspace/doris-flink-connector
RUN cd flink-doris-connector && \
    echo "6" | bash build.sh

# Final stage
FROM ghcr.io/apache/flink-kubernetes-operator:1.12.0

# Ensure the lib directory exists
ARG LIB_DIR=${FLINK_HOME}/lib
RUN mkdir -p ${LIB_DIR}

# Copy Flink Doris Connector jar from builder
COPY --from=builder /workspace/doris-flink-connector/dist/flink-doris-*.jar ${LIB_DIR}/flink-doris-connector.jar
