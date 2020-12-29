.PHONY: install docker-test

default: install

install:
	git submodule update --init --recursive
	sudo apt-get install -y \
		g++ \
		python-is-python2 \
		monkeysphere \
		python-dev-is-python2
	cd submodules/pycrypto && python setup.py build && sudo python setup.py install
	cd submodules/pexpect && python setup.py build && sudo python setup.py install
	sudo cp -R submodules/ptyprocess/ptyprocess /usr/local/lib/python2.7/dist-packages/

docker-test:
	docker build -t gpg-hd .
	mkdir -p keys
	docker run \
		--rm \
		-v "$$PWD/keys:/home/deterministic/gpg-hd/keys" \
		-it gpg-hd /home/deterministic/gpg-hd/gpg-hd.py "test seed" "test human" "test@test.com"
