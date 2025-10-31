FROM apache/doris:fe-3.1.1

ARG DORIS_HOME=/opt/apache-doris/fe

# Download connectors
RUN mkdir -p ${DORIS_HOME}/connectors
RUN curl -L -o /tmp/trino-bigquery.tar.gz https://github.com/apache/Doris-thirdparty/releases/download/trino-435-20240724/trino-bigquery-435-20240724.tar.gz && \
    tar -xzf /tmp/trino-bigquery.tar.gz -C ${DORIS_HOME}/connectors && \
    rm /tmp/trino-bigquery.tar.gz

# Download JDBC drivers
ARG POSTGRESQL_JDBC_VERSION=42.7.5
ARG MYSQL_JDBC_VERSION=9.2.0

RUN mkdir -p ${DORIS_HOME}/jdbc_drivers
RUN curl -L -o ${DORIS_HOME}/jdbc_drivers/postgresql.jar https://repo1.maven.org/maven2/org/postgresql/postgresql/$POSTGRESQL_JDBC_VERSION/postgresql-$POSTGRESQL_JDBC_VERSION.jar
RUN curl -L -o ${DORIS_HOME}/jdbc_drivers/mysql-connector-j.jar https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/$MYSQL_JDBC_VERSION/mysql-connector-j-$MYSQL_JDBC_VERSION.jar
