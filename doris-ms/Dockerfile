ARG VERSION=3.0.5
FROM apache/doris:ms-$VERSION

ARG DORIS_HOME=/opt/apache-doris/ms

# Move chmod 550 out of the start.sh script
# This is a workaround for the issue with the chmod command in the start.sh script
RUN sed -i '/chmod 550 "${DORIS_HOME}\/lib\/doris_cloud"/d' ${DORIS_HOME}/bin/start.sh
RUN chmod 550 ${DORIS_HOME}/lib/doris_cloud
