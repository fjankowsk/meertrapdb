BLK         =   black
DCK         =   docker
PIP         =   pip3

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
	@echo 'make black           reformat the python files using black code formatter'
	@echo 'make clean           remove temporary files'
	@echo 'make init_db         initialise database'
	@echo 'make install         install the module locally'
	@echo 'make interactive     run an interactive shell'
	@echo 'make production      build docker image for production use'
	@echo 'make run_db          start the database'
	@echo 'make tests           run the regression tests'

black:
	${BLK} *.py */*.py */*/*.py

clean:
	rm -f ${SRCDIR}/*.pyc
	rm -rf ${SRCDIR}/__pycache__
	rm -rf ${SRCDIR}/*/__pycache__
	rm -rf ${BASEDIR}/build
	rm -rf ${BASEDIR}/dist
	rm -rf ${BASEDIR}/meertrapdb.egg-info

init_db:
	${DCK} run -it --rm \
	--mount "type=bind,source=${DBPATH},target=/var/lib/mysql" \
	--mount "type=bind,source=${RUNPATH},target=/var/run/mysqld" \
	meertrapdb \
	${PRODDIR}/scripts/init_database.sh

install:
	${PIP} install .

interactive:
	${DCK} run -it --network=host \
	--mount "type=bind,source=${DATAPATH},target=/data" \
	--mount "type=bind,source=${WEBPATH},target=/webserver" \
	--user ${USERID} \
	meertrapdb bash

production:
	${DCK} build \
	--build-arg USERID=${USERID} \
	--file ${DOCKERFILE} \
	--tag meertrapdb ${BASEDIR}

run_db:
	${DCK} run -it --rm --network=host \
	--mount "type=bind,source=${DBPATH},target=/var/lib/mysql" \
	--mount "type=bind,source=${RUNPATH},target=/var/run/mysqld" \
	--name meertrap_db meertrapdb \
	${PRODDIR}/scripts/start_database.sh

tests:
	${DCK} run -it --rm meertrapdb nose2

.PHONY: help black clean init_db install interactive production run_db tests
