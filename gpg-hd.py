#!/usr/bin/env python

# Special thanks to Arttu Kasvio's code for starting this
# Requirements: pycrypto, monkeysphere, gpg

import os
import subprocess
import sys
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
import ptyprocess
import pexpect
import hashlib
from hmac_drbg import *

# GPG / yubikeys won't allow adding subkeys keytocard with timestamp of unix epoch 0
# We will use timestamp of 1 (A second into 1970-01-01) to indicate this is GPG-HD generated keys
timeStamp = "1"

def GPG_get_masterkey():
  id = subprocess.Popen( \
    "gpg --homedir temp " \
    "--keyring trustedkeys.gpg " \
    "--list-keys | " \
    "tail -n +3 | awk \'{ print $1 }\' | grep -v \"pub\" | grep -v \"uid\" | tr -s \'\\n\' \'\\n\'", \
    stdout=subprocess.PIPE, \
    stdin=subprocess.PIPE, \
    shell=True \
    )
  return id.communicate()[0]

def GPG_get_keygrips():
  # Get keygrips
  kg = subprocess.Popen( \
    "gpg " \
    "--homedir temp " \
    "--keyring trustedkeys.gpg " \
    "--with-keygrip -K | " \
    "grep \"Keygrip\" | awk \'{ print $3 }\'", \
    stdout=subprocess.PIPE, \
    stdin=subprocess.PIPE, \
    shell=True \
    )
  return kg.communicate()[0]

def GPG_set_primary_key(keyID, timestamp):
  # Set masterkey as primary
  child = pexpect.spawn( \
    "bash -c \"{ echo uid 1; echo primary; echo q; echo y; echo y; } | " \
    "gpg " \
    "--homedir temp " \
    "--keyring trustedkeys.gpg " \
    "--faked-system-time=" + timestamp + \
    " --expert " \
    "--command-fd=0 " \
    "--status-fd=1 " \
    "--pinentry-mode=loopback " \
    "--edit-key " \
    + keyID \
    )
  child.interact()


def GPG_add_auth_subkey(parent_keyID, subkey_grip, timestamp):
  # Auth subkey
  child = pexpect.spawn( \
    "bash -c \"{ echo addkey; echo 13; echo S; echo E; echo A; echo Q; echo 0; echo save; } | " \
    "gpg " \
    "--homedir temp " \
    "--keyring trustedkeys.gpg " \
    "--faked-system-time=" + timestamp + \
    " --expert " \
    "--command-fd=0 " \
    "--status-fd=1 " \
    "--pinentry-mode=loopback " \
    "--edit-key " \
    + parent_keyID \
    )
  child.expect (["Enter the keygrip: ",  pexpect.EOF, pexpect.TIMEOUT])
  child.send(subkey_grip + "\r")
  child.interact()


def GPG_add_enc_subkey(parent_keyID, subkey_grip, timestamp):
  # Enc subkey
  child = pexpect.spawn( \
    "bash -c \"{ echo addkey; echo 13; echo S; echo Q; echo 0; echo save; } | " \
    "gpg --homedir temp " \
    "--keyring trustedkeys.gpg " \
    "--faked-system-time=" + timestamp + \
    " --expert " \
    "--command-fd=0 " \
    "--status-fd=1 " \
    "--pinentry-mode=loopback " \
    "--edit-key " \
    + parent_keyID \
    )
  child.expect (["Enter the keygrip: ", pexpect.EOF, pexpect.TIMEOUT])
  child.send(subkey_grip + "\r")
  child.interact()

def GPG_add_sig_subkey(parent_keyID, subkey_grip, timestamp):
  # Sig subkey
  child = pexpect.spawn( \
    "bash -c \"{ echo addkey; echo 13; echo E; echo Q; echo 0; echo save; } | " \
    "gpg " \
    "--homedir temp " \
    "--keyring trustedkeys.gpg " \
    "--faked-system-time="  + timestamp + \
    " --expert " \
    "--command-fd=0 " \
    "--status-fd=1 " \
    "--pinentry-mode=loopback " \
    "--edit-key " \
    + parent_keyID \
    )
  child.expect (["Enter the keygrip: ", pexpect.EOF, pexpect.TIMEOUT])
  child.send(subkey_grip + "\r")
  child.interact()

def GPG_import_keychain(keychain_filename):
    gpg_import = subprocess.Popen([ \
    'gpg', \
    '--homedir', 'temp', \
    '--no-default-keyring', \
    '--keyring','trustedkeys.gpg', \
    '--import', keychain_filename \
    ])
    gpg_import.communicate()


def GPG_create_key(user_id, seed):

  rand = DRBG(hashlib.sha512(seed).digest())
  key = RSA.generate(4096, rand.generate)

  # Since we're auto-generating the key, default the creation time to UNIX time of (timeStamp)
  os.environ['PEM2OPENPGP_TIMESTAMP'] = timeStamp

  # pem2openpgp "Foo Bar <fbar@linux.net>" < priv.pem | gpg --import
  pem2openpgp = subprocess.Popen(['pem2openpgp', user_id], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
  gpg_id = pem2openpgp.communicate(key.exportKey(pkcs=1))[0]

  os.system("mkdir -p temp")
  os.system("chmod 700 -R temp")
  os.environ['GNUPGHOME'] = "temp"

  gpg_import = subprocess.Popen([ \
    'gpg', '--homedir','temp','--no-default-keyring','--keyring','trustedkeys.gpg','--import'], \
    stdin=subprocess.PIPE)
  gpg_import.communicate(gpg_id)

  gpg_export = subprocess.Popen([ \
    'gpg','--homedir','temp','--no-default-keyring','--keyring','trustedkeys.gpg','--export-secret-keys','-a'], \
    stdout=subprocess.PIPE)
  privateKey = gpg_export.communicate()[0]


def GPG_export_keychain(keyID, private_filename, public_filename, ssh_filename):
  # Export full private keychain to file
  export = subprocess.Popen( \
    "gpg --homedir temp --keyring trustedkeys.gpg --armor --export-secret-keys " \
     + keyID, \
    stdout=subprocess.PIPE, \
    shell=True \
    )
  privateKeyChain = export.communicate()[0]
  keyChainfile = open(private_filename, "w")
  keyChainfile.write(privateKeyChain)
  keyChainfile.close()

  # Export full public keychain to file
  export = subprocess.Popen( \
    "gpg --homedir temp --keyring trustedkeys.gpg --armor --export " \
    + keyID, \
    stdout=subprocess.PIPE, \
    shell=True \
    )
  publicKeyChain = export.communicate()[0]
  keyChainfile = open(public_filename, "w")
  keyChainfile.write(publicKeyChain)
  keyChainfile.close()

  # Export SSH public key to file
  export = subprocess.Popen( \
    "gpg --homedir temp --keyring trustedkeys.gpg --export-ssh-key " \
    + keyID, \
    stdout=subprocess.PIPE, \
    shell=True \
    )
  ssh_key = export.communicate()[0]
  sshfile = open(ssh_filename, "w")
  sshfile.write(ssh_key)
  sshfile.close()

def GPG_card_write(keyID):
  #Write Auth key to card
  child = pexpect.spawn( \
    "bash -c \"{ echo key 1; echo keytocard; echo 3; echo y; } | " \
    "gpg " \
    "--homedir temp " \
    "--keyring trustedkeys.gpg " \
    " --expert " \
    "--command-fd=0 " \
    "--status-fd=1 " \
    "--edit-key " \
    + keyID \
    )
  child.interact()

  #Write Enc key to card
  child = pexpect.spawn( \
    "bash -c \"{ echo key 2; echo keytocard; echo 2; echo y; } | " \
    "gpg " \
    "--homedir temp " \
    "--keyring trustedkeys.gpg " \
    " --expert " \
    "--command-fd=0 " \
    "--status-fd=1 " \
    "--edit-key " \
    + keyID \
    )
  child.interact()

  #Write Sig key to card
  child = pexpect.spawn( \
    "bash -c \"{ echo key 3; echo keytocard; echo 1; echo y; } | " \
    "gpg " \
    "--homedir temp " \
    "--keyring trustedkeys.gpg " \
    " --expert " \
    "--command-fd=0 " \
    "--status-fd=1 " \
    "--edit-key " \
    + keyID \
    )
  child.interact()


if __name__ == '__main__':
  os.system("rm -rf temp *.asc keys/* > /dev/null 2>&1")
  os.system("killall gpg-agent scdaemon ssh-agent > /dev/null 2>&1")
  card_write = False
  print("\n")

  if(len(sys.argv) == 1):
    print ("usage: gpg-hd \"[bip39 phrase]\" [--card]")
    print ("usage: gpg-hd \"[bip39 phrase]\" \"[name]\" \"[email]\" [--card]")
    exit()
  if(len(sys.argv) >= 4):
    seed = sys.argv[1]
    name = sys.argv[2]
    email = sys.argv[3]
    if(sys.argv[len(sys.argv) - 1] == "--card"):
      card_write = True
  else:
    # get name/email for GPG id
    name = raw_input('Name: ')
    email= raw_input('Email: ')
    if(sys.argv[len(sys.argv) - 1] == "--card"):
      card_write = True
    else:
      if(raw_input('Write keys to card? [y/n]: ') == 'y'):
        card_write = True
    if(len(sys.argv) >= 2):
      seed = sys.argv[1]
    else:
      seed = raw_input('Seed: ')

  user_id = '%s <%s>' % (name, email)

  # CA masterkey is sha256 of input seed, and the three subkeys are recursive sha256 hashes of that
  masterkey_hash = hashlib.sha256(seed.encode()).hexdigest()
  authkey_hash = hashlib.sha256(masterkey_hash).hexdigest()
  enckey_hash = hashlib.sha256(authkey_hash).hexdigest()
  sigkey_hash = hashlib.sha256(enckey_hash).hexdigest()

  # Create master CA key
  GPG_create_key(user_id, masterkey_hash)
  masterkeyID = GPG_get_masterkey()

  # Create 3 subkeys
  GPG_create_key(user_id, authkey_hash)
  GPG_create_key(user_id, enckey_hash)
  GPG_create_key(user_id, sigkey_hash)

  # GPG needs grips for moving to subkeys
  keygrips = GPG_get_keygrips()

  # Assemble the keychain
  GPG_set_primary_key(masterkeyID, timeStamp)
  GPG_add_auth_subkey(masterkeyID, keygrips.split('\n')[1], timeStamp)
  GPG_add_enc_subkey(masterkeyID, keygrips.split('\n')[2], timeStamp)
  GPG_add_sig_subkey(masterkeyID, keygrips.split('\n')[3], timeStamp)

  os.system("mkdir -p keys")
  keys_path = os.path.join(os.path.dirname(__file__) , "keys")
  GPG_export_keychain(masterkeyID, \
    os.path.join(keys_path, "private_keychain.asc"), \
    os.path.join(keys_path, "public_keychain.asc"), \
    os.path.join(keys_path, "ssh_key.asc") \
    )

  # GPG is lame and doesn't like when we remove old keyIDs that are now attached to subkeys,
  # so lets start over with fresh keydb
  os.system("rm -rf temp && mkdir -p temp && chmod 700 -R temp")
  os.environ['GNUPGHOME'] = "temp"

  GPG_import_keychain(os.path.join(keys_path, "private_keychain.asc"))

  # just for show...
  print("\n\n\n")
  gpg_list = subprocess.Popen([ \
    'gpg','--homedir','temp','--no-default-keyring','--keyring','trustedkeys.gpg','--list-keys'])
  gpg_list.communicate()
  print("\n")
  print(os.path.join(keys_path, "private_keychain.asc") + " Created\n")
  print(os.path.join(keys_path, "public_keychain.asc") + " Created\n")
  print(os.path.join(keys_path, "ssh_key.asc") + " Created\n")

  if(card_write):
    GPG_card_write(masterkeyID)

  os.system("rm -rf temp")
