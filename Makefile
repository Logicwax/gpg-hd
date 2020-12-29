.PHONY: install docker-test

default: install

install:
	sudo apt-get install -y \
		monkeysphere \
		python-is-python2 \
		python-crypto \
		python-pexpect \
		python-ptyprocess

docker-test:
	docker build -t gpg-hd .
	mkdir -p keys
	docker run \
		--rm \
		-v "$$PWD/keys:/home/deterministic/gpg-hd/keys" \
		-it gpg-hd /home/deterministic/gpg-hd/gpg-hd.py "test seed" "test human" "test@test.com"
