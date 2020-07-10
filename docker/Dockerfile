FROM debian:stable

# meta data
LABEL maintainer="Fabian Jankowski"
LABEL description="Docker image for MeerTRAP database."

RUN apt-get update && apt-get install -y \
    curl \
    default-libmysqlclient-dev \
    gcc \
    gfortran \
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

# add smart history search
RUN echo "\"\e[A\":history-search-backward" >> /etc/skel/.inputrc && \
    echo "\"\e[B\":history-search-forward" >> /etc/skel/.inputrc

# add normal user
ARG USERID=1234
ARG USERNAME=meertrap
RUN adduser --disabled-password --gecos ${USERNAME} \
    --uid ${USERID} ${USERNAME}

# python packages
RUN pip3 install --upgrade pip

RUN pip3 install \
    astropy \
    healpy \
    ipython \
    matplotlib \
    mysqlclient \
    numpy \
    pandas \
    pony \
    pybind11 \
    pytz \
    pyyaml \
    requests \
    scipy

# install pygedm later, as it requires numpy's f2py
RUN pip3 install pygedm

# install our software in docker image
ARG SOFT_PATH="/software/meertrapdb"

RUN mkdir -p ${SOFT_PATH}
COPY . ${SOFT_PATH}
RUN chown -R ${USERID}:${USERID} ${SOFT_PATH}

ENV PYTHONPATH ${SOFT_PATH}:${PYTHONPATH}
WORKDIR ${SOFT_PATH}
