FROM ubuntu

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive \
    apt-get install -y \
    gpg \
    git \
    monkeysphere \
    python-is-python2 \
    python-crypto \
    python-pexpect \
    python-ptyprocess \
    make \
    sudo

RUN apt-get update
ENV HOME /home/deterministic
RUN useradd -m -s /bin/bash deterministic
RUN echo "deterministic ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/deterministic

WORKDIR /home/deterministic
USER deterministic
WORKDIR /home/deterministic
RUN git clone https://github.com/Logicwax/gpg-hd
WORKDIR /home/deterministic/gpg-hd
RUN make install
RUN mkdir -p keys
