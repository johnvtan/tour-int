all: run
.PHONY: all server client run

server:
	python3 tourint/manage.py runserver

client:
	npm start --prefix ./client

run:
	make server & make client
