.PHONY: install

default: install

install:
	git submodule update --init --recursive
	cd submodules/pycrypto && python setup.py build && sudo python setup.py install
