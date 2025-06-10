# Build stage
FROM maven:3-eclipse-temurin-8 AS builder

# Clone and build the Flink Doris Connector (option 6 is Flink version 1.20.x)
WORKDIR /workspace
RUN git clone https://github.com/thealtoclef/doris-flink-connector.git --branch master --depth 1
WORKDIR /workspace/doris-flink-connector
RUN cd flink-doris-connector && \
    echo "6" | bash build.sh

# Final stage
FROM flink:1.20.1

# Ensure the lib directory exists
ARG LIB_DIR=${FLINK_HOME}/lib
RUN mkdir -p ${LIB_DIR}

# Copy Flink Doris Connector jar from builder
COPY --from=builder /workspace/doris-flink-connector/dist/flink-doris-*.jar ${LIB_DIR}/flink-doris-connector.jar

# Download flink-cdc source connectors jars
ARG FLINK_CDC_VERSION=3.2.1
ARG SOURCE_CONNECTORS="mysql postgres"
RUN for connector in $SOURCE_CONNECTORS; do \
    wget -O ${LIB_DIR}/flink-sql-connector-${connector}-cdc-${FLINK_CDC_VERSION}.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-${connector}-cdc/${FLINK_CDC_VERSION}/flink-sql-connector-${connector}-cdc-${FLINK_CDC_VERSION}.jar; \
    done

# Download dependencies jars
## MySQL connector
# https://nightlies.apache.org/flink/flink-cdc-docs-release-3.2/docs/connectors/flink-sources/mysql-cdc/#sql-client-jar
ARG MYSQL_DRIVER_VERSION=8.0.27
RUN wget -O ${LIB_DIR}/mysql-connector-java-${MYSQL_DRIVER_VERSION}.jar \
    https://repo1.maven.org/maven2/mysql/mysql-connector-java/${MYSQL_DRIVER_VERSION}/mysql-connector-java-${MYSQL_DRIVER_VERSION}.jar
