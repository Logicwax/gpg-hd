.PHONY: install

default: install

install:
	git submodule update --init --recursive
	sudo apt-get install g++ python-is-python2 monkeysphere python-dev-is-python2
	cd submodules/pycrypto && python setup.py build && sudo python setup.py install
	cd submodules/pexpect && python setup.py build && sudo python setup.py install
	sudo cp -R submodules/ptyprocess/ptyprocess /usr/local/lib/python2.7/dist-packages/
