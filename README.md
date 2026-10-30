Deterministic GPG brainwallet keychain generator
=============================

GPG-HD is a deterministic full GPG keychain (CA key + 3 subkeys) generator using an input seed such as a BIP-39 phrase.  It also automates writing this keychain to Yubikeys and generates public SSH keys.  For those who don't want their digital identity to be tied to physical media in case of theft/loss/or electronic failure.  This Idea was prompted by [electrum](https://electrum.org/), DJB's blog [Entropy Attacks](http://blog.cr.yp.to/20140205-entropy.html), and Arttu Kasvio's [ deterministic GPG key project.](https://github.com/arttukasvio/deterministic)



Requirements
------------

* python3
* gpg

To write the subkeys to a Yubikey/smartcard with `--card`:

* pcscd
* python3-ykman (yubikit, YubiKey Manager's Python library, version 5.x)
* python3-cryptography

The RSA key derivation and the OpenPGP key packets are built in Python (`rsa_derive.py`), and the card is programmed directly through its OpenPGP applet. `gpg-hd`, `hmac_drbg.py` and `rsa_derive.py` must stay together in one directory.


Installation
------------

sudo apt-get install gpg python3 pcscd python3-ykman python3-cryptography

Or if you're really lazy:
`make install`  (will need sudo elevation)


How to use
----------

`./gpg-hd -h`

`./gpg-hd "some awesome BIP-39 seed ..."  [--card] [--card-master]`

`./gpg-hd --name="Satoshi Nakamoto" --email="satoshi@aol.com" [--card] [--card-master] "some awesome BIP-39 seed phrase ..."`

If the argument `--card` is supplied then GPG-HD will factory reset the inserted card and write the three subkeys (Encryption, Auth, Sig) to it. With `--card-master` the master key is written, after a factory reset, to a card of its own (insert the card for each when asked). The two options can be combined, e.g. `--card-master --card` writes the master key to one card and the subkeys to another.

By default GPG-HD uses 1970-01-1 (Unix epoch of 1 second) to signal a deterministic keychain.  Optionally one can over-ride this with `--date=unix_time_in_secs`
 while key expirations are defaulted to 2 years.

The keychain files are written to a `keys` sub-directory of the directory you run `gpg-hd` from (or of your home directory if that one is not writable), named after the master key's fingerprint (`<fingerprint>`) and split into two directories so that each can be copied to a disk/microSD card of its own:

* `keys/private/<fingerprint>.private.keychain.asc`: the whole keychain, to be kept offline
* `keys/public/<fingerprint>.public.asc`: public key
* `keys/public/<fingerprint>.public.ssh.key`: public SSH key

Only the files in `keys/public/` should ever touch an internet connected computer.

If any of these files already exist, `gpg-hd` stops; move them away first.


Testing
----------

If on a non-debian system, you can easily test with docker (needs to be installed):

`make docker-test`


Use Cases
----------

On an airgap machine, use a safe brainwallet such as [PortalWallet](https://github.com/Logicwax/PortalWallet) to generate a BIP-39 phrase:

`portalwallet("satoshi")` gives a phrase such as `fetch december jazz hood pact owner cloth apart impact then person actual`. Pass it, in quotes, as the first argument:

 `./gpg-hd "fetch december jazz hood pact owner cloth apart impact then person actual" --name="satoshi" --email="satoshi@aol.com"`

 or

 `./gpg-hd "fetch december jazz hood pact owner cloth apart impact then person actual" --name="satoshi" --email="satoshi@aol.com" --card` will create a yubikey (which you can also use for SSH authentication along with the exported SSH key)

 or

 `./gpg-hd "fetch december jazz hood pact owner cloth apart impact then person actual" --name="satoshi" --email="satoshi@aol.com" --card-master` will write the master key to a yubikey of its own, to keep safe for certifying and expiration changes

 or both on two yubikeys, the master key first and then the subkeys:

 `./gpg-hd "fetch december jazz hood pact owner cloth apart impact then person actual" --name="satoshi" --email="satoshi@aol.com" --card-master --card`


Deterministic by design
-----------------------

The same seed (and `--date`) always gives the same keychain. The RSA keys are derived with a frozen copy of the algorithm PyCrypto 2.6.1 used (`rsa_derive.py`), so a seed gives the same keychain on any system and with any Python version. `make test` checks the derivation against known-good values (If it ever fails, existing seeds would derive different keychains)
