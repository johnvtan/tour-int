PYTHON := python3
NPM := npm

all: run
.PHONY: all server client run

server:
	$(PYTHON) tourint/manage.py runserver

client:
	$(NPM) i --prefix ./client
	$(NPM) start --prefix ./client

run:
	make server & make client
