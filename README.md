Deterministic GPG brainwallet keychain generator
=============================

GPG-HD is a deterministic full GPG keychain (CA key + 3 subkeys) generator using an input seed such as a BIP-39 phrase.  It also automates writing this keychain to Yubikeys and generates public SSH keys.  For those who don't want their digital identity to be tied to physical media in case of theft/loss/or electronic failure.  This Idea was prompted by [electrum](https://electrum.org/), DJB's blog [Entropy Attacks](http://blog.cr.yp.to/20140205-entropy.html), and Arttu Kasvio's [ deterministic GPG key project.](https://github.com/arttukasvio/deterministic)



Requirements
------------

* gpg
* monkeysphere 
* python-is-python2
* python-crypto
* python-pexpect
* python-ptyprocess 



Installation
------------

sudo apt-get install gpg monkeysphere python-is-python2  python-crypto python-pexpect python-ptyprocess make


Or if you're really lazy: 
`make install`  (will need sudo elevation)

How to use
----------

`./gpg-hd -h`

`./gpg-hd "some awesome BIP-39 seed ..."  [--card]`

`./gpg-hd --name="Satoshi Nakamoto" --email="satoshi@aol.com" [--card] "some awesome BIP-39 seed phrase ..."`

If the argument `--card` is supplied then GPG-HD will attempt to write the three subkeys (Encryption, Auth, Sig) to a card such as a Yubikey. 

By default GPG-HD uses 1970-01-1 (Unix epoch of 1 second) to signal a deterministic keychain.  Optionally one can over-ride this with `--date=unix_time_in_secs`
 while key expirations are defaulted to 2 years.

Private and Public GPG keychain files + SSH public key are located in the `keys` sub-directory.


Testing
----------

If on a non-debian system, you can easily test with docker (needs to be installed):

`make docker-test`


Use Cases
----------

On an airgap machine, use a safe brainwallet such as [PortalWallet](https://github.com/Logicwax/PortalWallet) to generate a BIP-39 phrase:

`SEED = portalwallet("satoshi")`

 `SEED="fetch december jazz hood pact owner cloth apart impact then person actual"`

 `./gpg-hd $SEED --name="satoshi" --email="satoshi@aol.com"`

 or 

 `./gpg-hd $SEED --name="satoshi" --email="satoshi@aol.com" --card` will create a yubikey (which you can also use for SSH authentication along with the exported SSH key)
