FROM ghcr.io/actions/actions-runner:latest

# Install packages and clean up as root
USER root
RUN apt-get update && apt-get install -y \
    build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Switch back to the standard GitHub Actions runner user (1001)
USER 1001
