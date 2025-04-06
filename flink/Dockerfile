FROM flink:1.20

ARG FLINK_VERSION=1.20
ARG FLINK_DORIS_CONNECTOR_VERSION=25.0.0
ARG FLINK_CDC_VERSION=3.2.1
ARG MYSQL_DRIVER_VERSION=8.0.27

# Download flink-doris-connector jar
RUN wget -O ${FLINK_HOME}/lib/flink-doris-connector.jar \
    https://repository.apache.org/content/repositories/releases/org/apache/doris/flink-doris-connector-${FLINK_VERSION}/${FLINK_DORIS_CONNECTOR_VERSION}/flink-doris-connector-${FLINK_VERSION}-${FLINK_DORIS_CONNECTOR_VERSION}.jar

# Download flink-cdc source connectors jars
ARG SOURCE_CONNECTORS="mysql postgres"
RUN for connector in $SOURCE_CONNECTORS; do \
    wget -O ${FLINK_HOME}/lib/flink-sql-connector-${connector}-cdc-${FLINK_CDC_VERSION}.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-${connector}-cdc/${FLINK_CDC_VERSION}/flink-sql-connector-${connector}-cdc-${FLINK_CDC_VERSION}.jar; \
    done

# Download dependencies jars
## MySQL connector
# https://nightlies.apache.org/flink/flink-cdc-docs-release-3.2/docs/connectors/flink-sources/mysql-cdc/#sql-client-jar
RUN wget -O ${FLINK_HOME}/lib/mysql-connector-java-${MYSQL_DRIVER_VERSION}.jar \
    https://repo1.maven.org/maven2/mysql/mysql-connector-java/${MYSQL_DRIVER_VERSION}/mysql-connector-java-${MYSQL_DRIVER_VERSION}.jar
