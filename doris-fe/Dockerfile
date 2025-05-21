ARG VERSION=3.0.5
FROM apache/doris:fe-$VERSION

ARG DORIS_HOME=/opt/apache-doris/fe

# Download JDBC drivers
ARG POSTGRESQL_JDBC_VERSION=42.7.5
ARG MYSQL_JDBC_VERSION=9.2.0

RUN mkdir -p ${DORIS_HOME}/jdbc_drivers/
RUN curl -o ${DORIS_HOME}/jdbc_drivers/postgresql.jar https://repo1.maven.org/maven2/org/postgresql/postgresql/$POSTGRESQL_JDBC_VERSION/postgresql-$POSTGRESQL_JDBC_VERSION.jar
RUN curl -o ${DORIS_HOME}/jdbc_drivers/mysql-connector-j.jar https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/$MYSQL_JDBC_VERSION/mysql-connector-j-$MYSQL_JDBC_VERSION.jar
