FROM codercom/code-server:latest

USER root

# System packages
RUN apt-get update && apt-get install -y \
        sudo \
        curl \
        build-essential \
        zip \
        unzip \
        lazygit \
    && rm -rf /var/lib/apt/lists/*

RUN echo "coder ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/coder \
    && chmod 0440 /etc/sudoers.d/coder

# Go
RUN GO_VERSION=$(curl -s https://go.dev/VERSION?m=text | head -1) \
    && curl -LO "https://go.dev/dl/${GO_VERSION}.linux-amd64.tar.gz" \
    && tar -C /usr/local -xzf "${GO_VERSION}.linux-amd64.tar.gz" \
    && rm "${GO_VERSION}.linux-amd64.tar.gz"
ENV PATH="/usr/local/go/bin:${PATH}"

# Node
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs

USER coder

# uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/coder/.local/bin:${PATH}"

# Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/home/coder/.cargo/bin:${PATH}"

# Java
RUN curl -s "https://get.sdkman.io?rcupdate=false" | bash \
 && bash -c "source /home/coder/.sdkman/bin/sdkman-init.sh \
    && echo 'sdkman_selfupdate_feature=false' >> /home/coder/.sdkman/etc/config \
    && JAVA_VERSION=\$(sdk list java | grep -oE '17\.[0-9]+\.[0-9]+-tem' | head -1) \
    && echo \"Installing Java \${JAVA_VERSION}\" \
    && sdk install java \${JAVA_VERSION}"
ENV SDKMAN_DIR="/home/coder/.sdkman"
ENV JAVA_HOME="/home/coder/.sdkman/candidates/java/current"
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Bun
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/home/coder/.bun/bin:${PATH}"

# Claude Code
RUN curl -fsSL https://claude.ai/install.sh | bash
