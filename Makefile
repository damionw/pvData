NOTEBOOK_PORT := 5100

.PHONY: clean help notebook console virtualenv

help:
        @echo "Usage: make all|env|clean|setup|console"

all: env setup

install:
	@pip install --upgrade bokeh==0.9.0 IPython==3.0.0 jsonschema
	@python setup.py install

virtualenv: env
	@(. env/bin/activate; make install)

console: virtualenv
	@(. env/bin/activate; exec pv_console)

notebook: virtualenv
	@(. env/bin/activate; exec ipython notebook --notebook-dir=pvData/notebooks --no-browser --port=$(NOTEBOOK_PORT))

env:
	virtualenv --system-site-packages $@

clean:
	-@rm -rf env dist build *.egg-info
