FROM flink:1.20

ARG FLINK_CDC_VERSION=3.2.1
ARG MYSQL_DRIVER_VERSION=8.0.27

# Ensure the lib directory exists
ARG LIB_DIR=${FLINK_HOME}/lib
RUN mkdir -p ${LIB_DIR}

# Copy local jars to the lib directory
COPY lib/* ${LIB_DIR}/

# Download flink-cdc source connectors jars
ARG SOURCE_CONNECTORS="mysql postgres"
RUN for connector in $SOURCE_CONNECTORS; do \
    wget -O ${LIB_DIR}/flink-sql-connector-${connector}-cdc-${FLINK_CDC_VERSION}.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-${connector}-cdc/${FLINK_CDC_VERSION}/flink-sql-connector-${connector}-cdc-${FLINK_CDC_VERSION}.jar; \
    done

# Download dependencies jars
## MySQL connector
# https://nightlies.apache.org/flink/flink-cdc-docs-release-3.2/docs/connectors/flink-sources/mysql-cdc/#sql-client-jar
RUN wget -O ${LIB_DIR}/mysql-connector-java-${MYSQL_DRIVER_VERSION}.jar \
    https://repo1.maven.org/maven2/mysql/mysql-connector-java/${MYSQL_DRIVER_VERSION}/mysql-connector-java-${MYSQL_DRIVER_VERSION}.jar
