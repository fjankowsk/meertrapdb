PY?         =   python
DCK	    	=   docker

BASEDIR     =   $(CURDIR)
SRCDIR      =   ${BASEDIR}/meertrapdb
PRODDIR     =   /software/meertrapdb
DOCKERFILE  =   ${BASEDIR}/docker/Dockerfile
MYSQLPORT   =   3310

help:
	@echo 'Makefile for Meertrap DB'
	@echo 'Usage:'
	@echo 'make production      build docker image for production use'
	@echo 'make clean           remove temporary files'
	@echo 'make interactive     run an interactive shell'
	@echo 'make run_db          start the database'
	@echo

production:
	${DCK} build --file ${DOCKERFILE} --tag meertrapdb ${BASEDIR}

clean:
	rm -f ${SRCDIR}/*.pyc
	rm -rf ${BASEDIR}/build
	rm -rf ${BASEDIR}/dist
	rm -rf ${BASEDIR}/meertrapdb.egg-info

interactive:
	${DCK} run -it --rm meertrapdb bash

run_db:
	${DCK} run -it --rm --publish ${MYSQLPORT}:${MYSQLPORT} --name meertrap_db meertrapdb \
	${PRODDIR}/scripts/start_database.sh

.PHONY: help production clean interactive run_db