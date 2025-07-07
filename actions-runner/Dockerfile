FROM ghcr.io/actions/actions-runner:latest

# Install system dependencies as root
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
        # Basic build tools
        build-essential \
        # Required for OpenSSL
        pkg-config \
        libssl-dev \
        # Required for bindgen
        clang \
        libclang-dev \
        # Required for GSSAPI/Kerberos
        libgssapi-krb5-2 \
        libkrb5-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Switch to the standard GitHub Actions runner user (1001)
USER 1001

# Set up Rust environment
ENV RUSTUP_HOME=/home/runner/.rustup \
    CARGO_HOME=/home/runner/.cargo \
    PATH=/home/runner/.cargo/bin:${PATH} \
    # Helpful for debugging
    RUST_BACKTRACE=1 \
    # Required for bindgen
    LIBCLANG_PATH=/usr/lib/llvm-16/lib

# Install Rust as non-root user
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable \
    # Add useful components
    && . $HOME/.cargo/env \
    && rustup component add rustfmt clippy \
    # Verify installation
    && rustc --version \
    && cargo --version
