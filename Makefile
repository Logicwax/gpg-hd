.PHONY: install test docker-test clean

default: install

clean:
	rm -rf *.pyc keys temp

install:
	sudo apt-get install -y \
		gpg \
		python3 \
		pcscd \
		tree \
		python3-ykman \
		python3-cryptography

test:
	python3 -B tests/test_rsa_derive.py

docker-test:
	docker build -t gpg-hd .
	rm -rf keys && mkdir -p keys
	docker run \
		--rm \
		-v "$$PWD/keys:/home/deterministic/keys" \
		-it gpg-hd /home/deterministic/gpg-hd --name="test human" --email="test@test.com" "test seed"
