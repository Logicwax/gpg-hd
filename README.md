Deterministic GPG brainwallet keychain generator
=============================

GPG-HD is a deterministic full GPG keychain (CA key + 3 subkeys) generator using an input seed such as a BIP-39 phrase.  It also automates writing this keychain to Yubikeys.  For those who don't want their digital identity to be tied to physical media in case of theft/loss/or electronic failure.  This Idea was prompted by [electrum](https://electrum.org/), DJB's blog [Entropy Attacks](http://blog.cr.yp.to/20140205-entropy.html), and Arttu Kasvio's [ deterministic GPG key project.](https://github.com/arttukasvio/deterministic)



Requirements
------------

* apt-get install gpg monkeysphere python-is-python2 python-dev-is-python2 \
python-crypto python-pexpect python-ptyprocess make 


Installation
------------

`make install`  (will need sudo elevation)

* All python modules included to help aide in portability (for airgap)

How to use
----------

`./gpg-hd`

`./gpg-hd "some awesome BIP-39 seed ..."  [--card]`

`./gpg-hd "some awesome BIP-39 seed ...." "Satoshi Nakamoto" "satoshi@aol.com" [--card]`

If the last argument is `--card` then GPG-HD will attempt to write the three subkeys (Encryption, Auth, Sig) to a card such as a Yubikey. 


Private and Public GPG keychain files + SSH public key are located in the `keys` sub-directory.


Testing
----------

If on non-debian system, but you have docker:

`make docker-test`


Use Cases
----------

On an airgap machine, use a safe brainwallet such as [PortalWallet](https://github.com/Logicwax/PortalWallet) to generate a BIP-39 phrase:

`SEED = portalwallet("satoshi")`

 `SEED="fetch december jazz hood pact owner cloth apart impact then person actual"`

 `./gpg-hd $SEED "satoshi" "satoshi@aol.com"`
