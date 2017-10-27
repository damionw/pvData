NOTEBOOK_PORT := 5005

.PHONY: clean help notebook console setup

help:
        @echo "Usage: make all|env|clean|setup|console"

all: env setup

console: setup env
	@(. env/bin/activate; exec pv_console)

notebook: setup env
	@(. env/bin/activate; exec ipython notebook --notebook-dir=pvData/notebooks --no-browser --port=$(NOTEBOOK_PORT))

setup: env
	@(. env/bin/activate; exec python setup.py install)

env:
	virtualenv --system-site-packages $@
	@(. env/bin/activate; pip install --upgrade bokeh==0.9.0 IPython==3.0.0)

clean:
	-@rm -rf env dist build *.egg-info
