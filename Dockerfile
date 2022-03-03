# Ubuntu focal as of 03/03/2022
FROM ubuntu@sha256:669e010b58baf5beb2836b253c1fd5768333f0d1dbcb834f7c07a4dc93f474be

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive \
    apt-get install -y \
    gpg \
    git \
    monkeysphere \
    python3-crypto \
    python3-pexpect

ENV HOME /home/deterministic
RUN useradd -m -s /bin/bash deterministic

WORKDIR /home/deterministic
USER deterministic
WORKDIR /home/deterministic
COPY . /home/deterministic/
WORKDIR /home/deterministic/
RUN mkdir -p keys
