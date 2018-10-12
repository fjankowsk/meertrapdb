FROM debian:stable

RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    git \
    make \
    mariadb-server \
    mariadb-client \
    netcat \
    net-tools \
    python2.7 \
    python2.7-dev \
    python-setuptools \
    vim \
 && rm -rf /var/lib/apt/lists/*

# mariadb configuration
ENV MYSQL_ROOT_PASSWORD=mariadb_test

# preparation for mariadb
RUN rm -rf /var/lib/mysql \
    && mkdir -p /var/lib/mysql /var/run/mysqld \
    && chown -R mysql:mysql /var/lib/mysql /var/run/mysqld \
    && chmod 777 /var/run/mysqld \
    && mysql_install_db

RUN easy_install pip
RUN pip install --upgrade pip