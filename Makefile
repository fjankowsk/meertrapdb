PY?         =   python
DCK	    	=   docker

BASEDIR     =   $(CURDIR)
SRCDIR      =   ${BASEDIR}/src
PRODDIR     =   /software/meertrapdb
DOCKERFILE  =   ${BASEDIR}/docker/Dockerfile

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

interactive:
	${DCK} run -it --rm meertrapdb bash

run_db:
	${DCK} run -it --rm meertrapdb ${PRODDIR}/scripts/start_database.sh

.PHONY: help production clean interactive run_db