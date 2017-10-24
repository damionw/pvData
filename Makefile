.PHONY: clean env

all: env setup

console: setup env
	@(. env/bin/activate; exec pv_console)

setup: env
	@(. env/bin/activate; exec python setup.py install)

env:
	virtualenv --system-site-packages $@

clean:
	-@rm -rf env
