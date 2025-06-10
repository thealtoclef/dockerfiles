# Build stage
FROM maven:3-eclipse-temurin-17 AS builder

# Clone and build the BigQuery Connector Plugin
WORKDIR /workspace
RUN git clone https://github.com/apache/doris-thirdparty.git --branch trino-435 --depth 1
WORKDIR /workspace/doris-thirdparty/plugin/trino-bigquery
RUN mvn clean install -DskipTests

# Final stage
FROM apache/doris:be-3.0.5

ARG DORIS_HOME=/opt/apache-doris/be

# Copy connectors from builder
RUN mkdir -p ${DORIS_HOME}/connectors
COPY --from=builder /workspace/doris-thirdparty/plugin/trino-bigquery/target/trino-bigquery-435 ${DORIS_HOME}/connectors/

# Download JDBC drivers
ARG POSTGRESQL_JDBC_VERSION=42.7.5
ARG MYSQL_JDBC_VERSION=9.2.0

RUN mkdir -p ${DORIS_HOME}/jdbc_drivers/
RUN curl -o ${DORIS_HOME}/jdbc_drivers/postgresql.jar https://repo1.maven.org/maven2/org/postgresql/postgresql/$POSTGRESQL_JDBC_VERSION/postgresql-$POSTGRESQL_JDBC_VERSION.jar
RUN curl -o ${DORIS_HOME}/jdbc_drivers/mysql-connector-j.jar https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/$MYSQL_JDBC_VERSION/mysql-connector-j-$MYSQL_JDBC_VERSION.jar

# Move chmod 550 out of the start_be.sh script
# This is a workaround for the issue with the chmod command in the start_be.sh script
RUN sed -i '/chmod 550 "${DORIS_HOME}\/lib\/doris_be"/d' ${DORIS_HOME}/bin/start_be.sh
RUN chmod 550 ${DORIS_HOME}/lib/doris_be
