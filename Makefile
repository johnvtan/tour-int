PYTHON := python3
NPM := npm

all: run
.PHONY: all server client run

server:
	$(PYTHON) backend/manage.py runserver

client:
	$(NPM) start --prefix ./client

run:
	make server & make client
