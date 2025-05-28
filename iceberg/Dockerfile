# Optimized Dockerfile to build Iceberg JARs for staging layer usage
FROM gradle:8.14.1-jdk17

# Argument for specific commit SHA
ARG COMMIT=4e0207ad10cc5f770bfbfcddd5ff4107abcca896

# Clone and checkout specific commit in single layer
WORKDIR /src
RUN git clone --depth 1 https://github.com/apache/iceberg.git . && \
    git fetch --unshallow && \
    git checkout $COMMIT

# Build with Gradle
RUN ./gradlew build -x test -x integrationTest -d /dist

WORKDIR /dist

# Simple output for staging layer usage
CMD ["ls", "-la", "/dist"]
