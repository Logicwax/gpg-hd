# Ubuntu 26.04.1 LTS (resolute) as of 10/30/2026
FROM ubuntu@sha256:6a06111c3b0a8600feadb270aec771dc239bf407b25625f93f44ab00e11f4d3c

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    gpg \
    python3 \
    pcscd \
    python3-ykman \
    python3-cryptography \
    && rm -rf /var/lib/apt/lists/*

ENV HOME=/home/deterministic
# uid 1000 like the user on a typical host, so a mounted keys/ directory is writable (the base image's own
# default user has it, hence the userdel)
RUN userdel -r ubuntu 2>/dev/null; useradd -m -u 1000 -s /bin/bash deterministic

USER deterministic
WORKDIR /home/deterministic
COPY --chown=deterministic:deterministic . /home/deterministic/
RUN mkdir -p keys
