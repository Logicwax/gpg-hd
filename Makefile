.PHONY: install docker-test clean

default: install

clean:
	rm -rf *.pyc keys temp

install:
	sudo apt-get install -y \
		gpg \
		monkeysphere \
		python3-crypto \
		python3-pexpect \

docker-test:
	docker build -t gpg-hd .
	mkdir -p keys
	docker run \
		--rm \
		-v "$$PWD/keys:/home/deterministic/keys" \
		-it gpg-hd /home/deterministic/gpg-hd --name="test human" --email="test@test.com" "test seed"
