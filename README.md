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











Janoher
=========

On MacOS:

`Step 1: Get Homebrew`
 
`Step 2: $: brew install gpg`
 
`Step 3: $: brew install monkeysphere`
 
`Step 4: $: cd to this directory`
 
`Step 5: $: pip install virtualenv`
 
`Step 6: $: virtualenv -p /usr/bin/python2.7 virtual`
 
`Step 7: $: source virtual/bin/activate`
 
`Step 8: $: pip install -r mac.txt`
 
`Step 9: $: ./gpg-hd --name="[NAME]" --email="[EMAIL]" --date=[DATE] "[BIP-39]"`


`Step 10: Import private key into GPG Keychain Suite, and then change primary key's expiration date to NONE.`
 
`Step 11: Add a passcode to your key.`
 
`Step 12: Export public key so that others can send you encrypted messages/files.`
 
`Step 13: Decrypt messages/files using GPG Keychain Suite Services.`


   Note: Public key can never be recreated again, but you can always decrypt any message/file sent to that public key with either the master key or any sub-keys generated from the master key.

   Done!








































