.PHONY: install

default: install

install:
	sudo apt-get install python-is-python2 monkeysphere python-dev-is-python2
	git submodule update --init --recursive
	cd submodules/pycrypto && python setup.py build && sudo python setup.py install
	cd submodules/pyexpect && python setup.py build && sudo python setup.py install
