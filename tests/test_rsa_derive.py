#!/usr/bin/env python3
"""Pins the frozen key derivation of rsa_derive.py (see its docstring) to ground truth.

The expected values were produced by PyCrypto 2.6.1's RSA.generate and exportKey(pkcs=1) and by monkeysphere's
pem2openpgp 0.41 for the seed "test seed one": SHA-256 of the decimal modulus, of the PKCS#1 PEM and of the
OpenPGP packets for the user ID "Test Human <test@test.com>" with creation time 1. If this fails, every
existing seed would derive a different keychain: fix the code, never the numbers.

    python3 tests/test_rsa_derive.py   (or: make test; about half a minute: four 4096 bit keys in pure Python)
"""

import hashlib
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import rsa_derive
from hmac_drbg import DRBG

SEED = "test seed one"
UID = "Test Human <test@test.com>"

# name: (sha256 of str(n), sha256 of the PEM, sha256 of the openpgp_secret_key packets)
EXPECTED = {
    "master": ("d0ed86dc44805e25e175d6f54fa026e1dfa291fcce66316ace010edd41313f09",
               "dde05d3a5ab114a71b227ef6f6e7044769241fdf52ef217949547ebf22e2943e",
               "2abdb1697b38f3c7715ae6aab8164f94877ba0c754641e560433be7529be1032"),
    "auth": ("7226ebbd9687d95372db09bfdc434e9cf87e9788f90e2bb219cf1ac8e49d52ed",
             "eb68841430f7c49d25eae50a958cba6641969ee3614c7a8949526f5ce3303556",
             "0464b45d8f63cc27c9700aace65de93ff58883f06aa794640562602f14f98ef1"),
    "enc": ("7abdf90ef72530188aae0a2eb4cf0e0fb1a22311e4f0b51011d934e6c690c12d",
            "ce2e83bee0b5f3de94e88a8dca08e1c0ae8c2407f8a11b461d033003a1c44686",
            "b5438d33cc1ffe256478145bceada2472aef26441cbf438a2e973666170bf60a"),
    "sig": ("77c3c899053bb011f4e3497bb6338e4bc60c8b8446cc3c900ccc1cac6bb443da",
            "e463633b6350051c5d9d0d2500d2b20606129e63914e2d14091e28589a658d52",
            "8b99067ebc97874307c8ebae8e0c2833d7d1670c4ff602c01956492ee93cf491"),
}


def seed_chain(seed):
  # same chain gpg-hd uses: master = sha256(seed), then each key's hash is the sha256 of the previous one
  master = hashlib.sha256(seed.encode()).hexdigest().encode()
  auth = hashlib.sha256(master).hexdigest().encode()
  enc = hashlib.sha256(auth).hexdigest().encode()
  sig = hashlib.sha256(enc).hexdigest().encode()
  return {"master": master, "auth": auth, "enc": enc, "sig": sig}


class DerivationTest(unittest.TestCase):
  def test_known_keys(self):
    for name, seed in seed_chain(SEED).items():
      key = rsa_derive.generate(4096, DRBG(hashlib.sha256(seed).digest()).generate)
      n_hash, pem_hash, packet_hash = EXPECTED[name]
      self.assertEqual(hashlib.sha256(str(key.n).encode()).hexdigest(), n_hash, name + " modulus")
      self.assertEqual(hashlib.sha256(key.export_pem_pkcs1()).hexdigest(), pem_hash, name + " PEM")
      self.assertEqual(hashlib.sha256(key.openpgp_secret_key(UID, 1)).hexdigest(), packet_hash, name + " packets")


if __name__ == "__main__":
  unittest.main()
