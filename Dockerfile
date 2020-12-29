FROM ubuntu

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive \
    apt-get install -y \
    git \
    make \
    sudo \
    g++ \
    python-is-python2 \
    monkeysphere \
    python-dev-is-python2

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
