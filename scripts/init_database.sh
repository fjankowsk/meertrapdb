#!/usr/bin/env bash
#
# Simple wrapper to initialise database. 
# 2019 Fabian Jankowski
#

mkdir -p /var/lib/mysql /var/run/mysqld
chown -R mysql:mysql /var/lib/mysql /var/run/mysqld
chmod 777 /var/run/mysqld
mysql_install_db
