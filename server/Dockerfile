# syntax=docker/dockerfile:1
FROM nvidia/cuda:11.6.0-devel-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive
ARG TZ=Europe/London

ARG app_user
ARG uid
ARG gid
ARG marian_compile_server
ARG release_wheel

ENV USER=$app_user
ENV UID=$uid
ENV GID=$gid
ENV HOME=/home/$USER
ENV APP_DIR=$HOME/app
ENV RELEASE_WHEEL=/tmp/$release_wheel

RUN build_deps="curl" && \
    apt update && \
    apt install -y --no-install-recommends ${build_deps} ca-certificates && \
    curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
    apt install -y git-lfs && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt update -y && apt upgrade -y && apt install -y \
    tzdata locales git-core pkg-config libtool \
    git cmake build-essential libboost-system-dev \
    libprotobuf17 protobuf-compiler libprotobuf-dev \
    openssl libssl-dev libgoogle-perftools-dev \
    python3-dev python3-pip python3-venv python3-setuptools \
    hunspell libhunspell-dev

# Set the locale.
ENV LANG="en_GB.UTF-8"
ENV LANGUAGE="en_GB:en"
ENV MARIANPATH=$HOME/marian-nmt
ENV CONDA_HOME=$HOME/conda
ENV PATH=$MARIANPATH/build:$CONDA_HOME/bin:$USER/.local/bin:$PATH

# Make the application available via PYTHONPATH.
ENV PYTHONPATH=$APP_DIR

RUN locale-gen cy_GB.UTF-8

# Setup non-root user
SHELL ["/bin/bash", "--login", "-c"]

# root commands
RUN addgroup --gid $GID $app_user
RUN adduser --disabled-password \
            --gecos "Non root user" \
            --uid $UID \
            --gid $GID \
            --home $HOME $USER

RUN mkdir -p $USER/.local/bin
RUN echo "export PATH=$USER/.local/bin:$PATH" >> $USER/.bashrc

# Non root actions from here on.
USER $USER

# Build Marian.
RUN git clone https://github.com/marian-nmt/marian $MARIANPATH && \
    cd $MARIANPATH && \
    git checkout tags/1.10.0 -b 1.10.0 && \
    mkdir -p $MARIANPATH/build

WORKDIR $MARIANPATH/build
RUN cmake $MARIANPATH \
    -DUSE_SENTENCEPIECE=on \
    -DCOMPILE_CUDA=on \
    -DCOMPILE_SERVER=${marian_compile_server} && make -j `nproc`

# Install moses scripts.
WORKDIR $MARIANPATH/scripts
RUN git clone https://github.com/marian-nmt/moses-scripts.git

# Setup and install conda, use for python.
RUN curl -o miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-py39_4.11.0-Linux-x86_64.sh && \
    sh miniconda.sh -b -p $CONDA_HOME && \
    echo PATH=$CONDA_HOME/bin:$PATH >> $HOME/.bashrc && \
    conda install -c conda-forge cld2-cffi

COPY supervisord.conf .env $HOME/

# .whl file should only exist if doing a release.
COPY requirements.txt *.whl /tmp/

# Install app requirements.
RUN $CONDA_HOME/bin/python -m pip install --no-cache-dir -r /tmp/requirements.txt
RUN if [[ ! -z $release_wheel ]] ; then echo "Installing $RELEASE_WHEEL" && $CONDA_HOME/bin/python -m pip install $RELEASE_WHEEL; else echo "RELEASE WHEEL NOT FOUND: $RELEASE_WHEEL"; fi

WORKDIR $HOME
