"""Frozen RSA key derivation for gpg-hd.

gpg-hd must turn the same seed into the same GPG keychain, forever.  The RSA keys it derives were originally
produced by PyCrypto 2.6.1 (python3-crypto): RSA.generate(4096, randfunc) with its C accelerator (_fastmath),
fed from the HMAC_DRBG in hmac_drbg.py.  PyCrypto is abandoned and general purpose crypto libraries are free to
change how they search for primes (PyCryptodome already generates different keys from the same random stream),
so the derivation lives here instead, as plain Python on top of Python's own integers: no third party
dependency that can change under it.

This is a line for line port of PyCrypto 2.6.1:
  * src/_fastmath.c   getRandomInteger, getRandomNBitInteger, getRandomRange, sieve_field, rabinMillerTest,
                      getStrongPrime
  * lib/Crypto/PublicKey/_RSA.py   generate_py   (the p, q, u, d assembly)
  * lib/Crypto/PublicKey/RSA.py    exportKey(pkcs=1)  (PKCS#1 PEM)
Details that matter for reproducing its output and that differ from "obvious" code:
  * random bytes are read as a LITTLE endian integer (bytes_to_mpz), one more byte than needed, shifted back down;
  * the random bases of the Miller-Rabin test are drawn from the same stream as the candidates, so how many bytes
    are consumed depends on which candidates turn out composite;
  * the sieve is the first 10000 primes;
  * the lower bound sqrt(2)*2^k is computed with GMP's default 64 bit mpf precision, so only the top 64 bits
    of sqrt(2) are kept (0xb504f333f9de6484);
  * d is the inverse of e modulo (p-1)(q-1), not the lcm; p < q.

It also builds the OpenPGP packets (secret key, user ID, self-signature) that gpg-hd used to get from
monkeysphere's pem2openpgp, which no longer exists in Debian and whose Perl RSA library now refuses the
PKCS#1 v1.5 padding it signs with. RSAKey.openpgp_secret_key() produces the same bytes as pem2openpgp 0.41
(timestamp pinned, no expiration, certify-only usage flags).

Do not "improve" any of this: any change makes every existing seed derive a different keychain.
tests/test_rsa_derive.py pins known outputs.
"""

import base64
import hashlib
import math
import struct

# The first 10000 primes (sieve_base in _fastmath.c).
def _first_primes(count):
  primes = []
  candidate = 2
  while len(primes) < count:
    if all(candidate % p for p in primes if p * p <= candidate):
      primes.append(candidate)
    candidate += 1
  return primes

SIEVE_BASE = _first_primes(10000)
FIELD_SIZE = 5 * len(SIEVE_BASE)

# floor(sqrt(2) * 2^63): GMP's mpf_sqrt_ui at the default 64 bit precision.
SQRT2_64 = math.isqrt(2 << 126)


def _random_integer(bits, randfunc):
  # getRandomInteger: bits/8 + 1 bytes, read little endian, then the surplus 1..8 bits shifted off.
  data = randfunc(bits // 8 + 1)
  return int.from_bytes(data, "little") >> (8 - bits % 8)


def _random_nbit_integer(bits, randfunc):
  # getRandomNBitInteger: sets bit number `bits`, so the result really has bits + 1 bits.
  return _random_integer(bits, randfunc) | (1 << bits)


def _random_range(lower, upper, randfunc):
  # getRandomRange: lower <= n < upper
  span = upper - lower - 1
  bits = span.bit_length()
  while True:
    n = _random_integer(bits, randfunc)
    if n <= span:
      return n + lower


def _rabin_miller(n, rounds, randfunc):
  # rabinMillerTest: 1 = probably prime, 0 = composite
  if n & 1 == 0 or n < 3:
    return 1 if n == 2 else 0
  n_1 = n - 1
  b = (n_1 & -n_1).bit_length() - 1        # mpz_scan1(n_1, 0)
  m = n_1 >> b
  if n < (1 << 64) and n - 2 < rounds:
    rounds = n - 2
  tested = []
  for _ in range(rounds):
    while True:
      a = _random_range(2, n, randfunc)
      if a not in tested:
        break
    tested.append(a)
    z = pow(a, m, n)
    if z == 1 or z == n_1:
      continue
    composite = True
    for _ in range(b):
      z = z * z % n
      if z == 1:
        return 0
      if z == n_1:
        composite = False
        break
    if composite:
      return 0
  return 1


def _sieve_field(start):
  field = bytearray(FIELD_SIZE)
  for prime in SIEVE_BASE:
    first = (prime - start % prime) % prime
    if first < FIELD_SIZE:
      field[first::prime] = b"\x01" * len(range(first, FIELD_SIZE, prime))
  return field


def _strong_prime(bits, e, false_positive_prob, randfunc):
  # getStrongPrime (Silverman, "Fast generation of random, strong RSA primes", 1997)
  if bits < 512 or bits % 128:
    raise ValueError("bits must be multiple of 128 and > 512")
  rounds = int(math.ceil(-math.log(false_positive_prob) / math.log(4)))
  x = (bits - 512) // 128
  lower = SQRT2_64 << (511 + 128 * x - 63)
  upper = (1 << (512 + 128 * x)) - 1

  X = _random_range(lower, upper, randfunc)
  y = [_random_nbit_integer(101, randfunc), _random_nbit_integer(101, randfunc)]

  p = []
  for start in y:
    field = _sieve_field(start)
    found = None
    for j in range(FIELD_SIZE):
      if field[j]:
        continue
      if _rabin_miller(start + j, rounds, randfunc) > 0:
        found = start + j
        break
    if found is None:
      raise RuntimeError("Couldn't find prime in field")
    p.append(found)

  # R = (p2^-1 mod p1) * p2 - (p1^-1 mod p2) * p1 ; start the search at Y0 = X + (R - X mod p1p2)
  R = pow(p[1], -1, p[0]) * p[1] - pow(p[0], -1, p[1]) * p[0]
  increment = p[0] * p[1]
  X = X + (R - X % increment)
  while True:
    possible = all(X % prime for prime in SIEVE_BASE)
    if possible and e and e & 1:
      possible = math.gcd(X - 1, e) == 1
    if possible and _rabin_miller(X, rounds, randfunc) > 0:
      return X
    X += increment
    if X >= upper:
      raise RuntimeError("Couldn't find prime in field")


class RSAKey:
  def __init__(self, n, e, d, p, q, u):
    self.n, self.e, self.d, self.p, self.q, self.u = n, e, d, p, q, u

  def _public_key_body(self, timestamp):
    return struct.pack(">BIB", 4, timestamp, 1) + _mpi(self.n) + _mpi(self.e)

  def fingerprint(self, timestamp):
    """The 20 byte OpenPGP v4 fingerprint this key has with the given creation time."""
    body = self._public_key_body(timestamp)
    return hashlib.sha1(struct.pack(">BH", 0x99, len(body)) + body).digest()

  def openpgp_secret_key(self, uid, timestamp):
    """What `PEM2OPENPGP_TIMESTAMP=<timestamp> pem2openpgp <uid> < key.pem` printed: the unprotected secret
    key packet, the user ID packet and a positive-certification self-signature (SHA-256, RSA PKCS#1 v1.5)."""
    pubkey = self._public_key_body(timestamp)
    secret = _mpi(self.d) + _mpi(self.p) + _mpi(self.q) + _mpi(self.u)
    seckey = pubkey + b"\x00" + secret + struct.pack(">H", sum(secret) & 0xFFFF)
    uid = uid.encode("utf-8")

    fingerprint = self.fingerprint(timestamp)
    hashed = (struct.pack(">BBB", 22, 33, 4) + fingerprint                       # issuer fingerprint
              + struct.pack(">BBI", 5, 2, timestamp)                            # signature creation time
              + bytes([2, 27, 0x01])                                            # key flags: certify
              + bytes([6, 11, 9, 8, 7, 3, 2])                                   # AES256 AES192 AES128 CAST5 3DES
              + bytes([7, 21, 10, 9, 8, 11, 3, 2])                              # SHA512 SHA384 SHA256 SHA224 RIPEMD160 SHA1
              + bytes([4, 22, 2, 3, 1])                                         # ZLIB BZip2 ZIP
              + bytes([2, 30, 0x01])                                            # features: MDC
              + bytes([2, 23, 0x80]))                                           # keyserver preferences: no-modify
    sig_data = bytes([4, 0x13, 1, 8]) + struct.pack(">H", len(hashed)) + hashed

    signed = (_packet(6, pubkey, min_length_octets=2) + struct.pack(">BI", 0xB4, len(uid)) + uid
              + sig_data + struct.pack(">BBI", 4, 0xFF, len(sig_data)))
    digest = hashlib.sha256(signed).digest()
    signature = pow(_emsa_pkcs1_v15_sha256(digest, (self.n.bit_length() + 7) // 8), self.d, self.n)

    issuer = bytes([9, 16]) + fingerprint[-8:]
    sig_body = sig_data + struct.pack(">H", len(issuer)) + issuer + digest[:2] + _mpi(signature)
    return _packet(5, seckey) + _packet(13, uid) + _packet(2, sig_body)

  def export_pem_pkcs1(self):
    """PKCS#1 RSAPrivateKey in PEM, byte for byte what PyCrypto's exportKey(pkcs=1) wrote."""
    values = [0, self.n, self.e, self.d, self.p, self.q,
              self.d % (self.p - 1), self.d % (self.q - 1), pow(self.q, -1, self.p)]
    body = b"".join(_der_integer(v) for v in values)
    der = b"\x30" + _der_length(len(body)) + body
    chunks = [base64.b64encode(der[i:i + 48]) + b"\n" for i in range(0, len(der), 48)]
    return b"-----BEGIN RSA PRIVATE KEY-----\n" + b"".join(chunks) + b"-----END RSA PRIVATE KEY-----"


def _mpi(n):
  # OpenPGP multiprecision integer: bit count, then the minimal big endian bytes
  return struct.pack(">H", n.bit_length()) + n.to_bytes((n.bit_length() + 7) // 8, "big")


def _packet(tag, body, min_length_octets=None):
  # old format packet header, as pem2openpgp's make_packet wrote it
  length = len(body)
  pseudo = max(length, 2 ** (8 * min_length_octets) - 1) if min_length_octets else length
  if pseudo < 2 ** 8:
    code, size = 0, 1
  elif pseudo < 2 ** 16:
    code, size = 1, 2
  else:
    code, size = 2, 4
  return bytes([0x80 + tag * 4 + code]) + length.to_bytes(size, "big") + body


_SHA256_DIGESTINFO = bytes.fromhex("3031300d060960864801650304020105000420")


def _emsa_pkcs1_v15_sha256(digest, em_length):
  padding = b"\xff" * (em_length - len(_SHA256_DIGESTINFO) - len(digest) - 3)
  return int.from_bytes(b"\x00\x01" + padding + b"\x00" + _SHA256_DIGESTINFO + digest, "big")


def _der_length(length):
  if length > 127:
    encoded = length.to_bytes((length.bit_length() + 7) // 8, "big")
    return bytes([len(encoded) + 128]) + encoded
  return bytes([length])


def _der_integer(value):
  payload = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
  if payload[0] > 127:
    payload = b"\x00" + payload
  return b"\x02" + _der_length(len(payload)) + payload


def generate(bits, randfunc, e=65537):
  """RSA.generate(bits, randfunc, e) as PyCrypto 2.6.1 did it with its C accelerator."""
  if bits < 1024 or bits & 0xff:
    raise ValueError("RSA modulus length must be a multiple of 256 and >= 1024")
  p = q = 1
  while (p * q).bit_length() < bits:
    p = _strong_prime(bits >> 1, e, 1e-12, randfunc)
    q = _strong_prime(bits - (bits >> 1), e, 1e-12, randfunc)
  if p > q:
    p, q = q, p
  u = pow(p, -1, q)
  n = p * q
  d = pow(e, -1, (p - 1) * (q - 1))
  return RSAKey(n, e, d, p, q, u)
