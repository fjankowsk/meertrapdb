PY?         =   python
DCK	    	=   docker

BASEDIR     =   $(CURDIR)
SRCDIR      =   ${BASEDIR}/meertrapdb
PRODDIR     =   /software/meertrapdb
DOCKERFILE  =   ${BASEDIR}/docker/Dockerfile
DBPATH      =   /raid/jankowsk/mariadb
RUNPATH     =   /raid/jankowsk/mariadb_run
DATAPATH    =   /raid/DWFcandidates/
WEBPATH     =   /raid/webhost/www/meerkatcands.com/html/meertrap_cands/candidates
USERID      =   $(shell id -u)


help:
	@echo 'Makefile for Meertrap DB'
	@echo 'Usage:'
	@echo 'make production      build docker image for production use'
	@echo 'make init_db         initialise database'
	@echo 'make clean           remove temporary files'
	@echo 'make interactive     run an interactive shell'
	@echo 'make run_db          start the database'

production:
	${DCK} build \
	--build-arg USERID=${USERID} \
	--file ${DOCKERFILE} \
	--tag meertrapdb ${BASEDIR}

init_db:
	${DCK} run -it --rm \
	--mount "type=bind,source=${DBPATH},target=/var/lib/mysql" \
	--mount "type=bind,source=${RUNPATH},target=/var/run/mysqld" \
	meertrapdb \
	${PRODDIR}/scripts/init_database.sh

clean:
	rm -f ${SRCDIR}/*.pyc
	rm -rf ${BASEDIR}/build
	rm -rf ${BASEDIR}/dist
	rm -rf ${BASEDIR}/meertrapdb.egg-info

interactive:
	${DCK} run -it --rm --network=host \
	--mount "type=bind,source=${DATAPATH},target=/data" \
	--mount "type=bind,source=${WEBPATH},target=/webserver" \
	--user ${USERID} \
	meertrapdb bash

run_db:
	${DCK} run -it --rm --network=host \
	--mount "type=bind,source=${DBPATH},target=/var/lib/mysql" \
	--mount "type=bind,source=${RUNPATH},target=/var/run/mysqld" \
	--name meertrap_db meertrapdb \
	${PRODDIR}/scripts/start_database.sh

.PHONY: help production init_db clean interactive run_db