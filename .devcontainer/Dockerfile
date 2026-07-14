FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# Add Yarn GPG key and APT repo securely
RUN curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --dearmor | tee /usr/share/keyrings/yarn-archive-keyring.gpg > /dev/null

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        gnupg \
    && rm -rf /var/lib/apt/lists/*
