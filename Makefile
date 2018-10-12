PY?         =   python
DCK	    	=   docker

BASEDIR     =   $(CURDIR)
SRCDIR		=	${BASEDIR}/src
DOCKERFILE  =   ${BASEDIR}/docker/Dockerfile

help:
	@echo 'Makefile for Meertrap DB'
	@echo 'Usage:'
	@echo 'make production      build docker image for production use'
	@echo

production:
	${DCK} build --file ${DOCKERFILE} --tag meertrapdb ${BASEDIR}

clean:
	rm ${SRCDIR}/*.pyc

.PHONY: help production clean
