FROM ghcr.io/actions/actions-runner:latest

# Install system dependencies as root
USER root
RUN apt-get update \
    && apt-get install -y \
        curl \
        build-essential \
        pkg-config \
        libssl-dev \
        libclang-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch to the standard GitHub Actions runner user (1001)
USER 1001

# Set environment variables for Rust and Cargo
ENV RUSTUP_HOME=/home/runner/.rustup \
    CARGO_HOME=/home/runner/.cargo \
    PATH=/home/runner/.cargo/bin:${PATH} \
    RUST_BACKTRACE=1 \
    LIBCLANG_PATH=/usr/lib/llvm-*/lib

# Install Rust as non-root user
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable \
    && rustup component add rustfmt clippy \
    && rustc --version \
    && cargo --version
