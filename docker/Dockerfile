FROM debian:stable

# meta data
LABEL maintainer="Fabian Jankowski"
LABEL description="Docker image for MeerTRAP database."

RUN apt-get update && apt-get install -y \
    curl \
    default-libmysqlclient-dev \
    gcc \
    git \
    make \
    mariadb-server \
    mariadb-client \
    netcat \
    net-tools \
    procps \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    vim \
 && rm -rf /var/lib/apt/lists/*

# preparation for mariadb
RUN rm -rf /var/lib/mysql \
    && mkdir -p /var/lib/mysql /var/run/mysqld \
    && chown -R mysql:mysql /var/lib/mysql /var/run/mysqld \
    && chmod 777 /var/run/mysqld \
    && mysql_install_db

RUN sed -i 's/3306/3310/' /etc/mysql/mariadb.conf.d/50-server.cnf

# smart history search
RUN echo "\"\e[A\":history-search-backward" >> ~/.inputrc && \
    echo "\"\e[B\":history-search-forward" >> ~/.inputrc

RUN pip3 install --upgrade pip

# python packages
RUN pip3 install \
    astropy \
    ipython \
    matplotlib \
    mysqlclient \
    numpy \
    pony \
    pyyaml \
    pytz

# install our software in docker image
ARG SOFT_PATH="/software/meertrapdb"

RUN mkdir -p ${SOFT_PATH}
COPY . ${SOFT_PATH}

ENV PYTHONPATH ${SOFT_PATH}:${PYTHONPATH}
WORKDIR ${SOFT_PATH}