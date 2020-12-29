import sys
import os.path
import hashlib
# Import from git submodule ... hackish ... is there a better way?
HMAC_DRBG_DIR = os.path.join(os.path.dirname(__file__), 'submodules', 'python_hmac_drbg', 'hmac_drbg')
if HMAC_DRBG_DIR not in sys.path:
  sys.path.insert(0, HMAC_DRBG_DIR)
import hmac_drbg

class HMAC_DRBG(object):
  """ Deterministic "random" generator using HMAC_DRBG 
      Some code from: https://github.com/dlitz/pycrypto/blob/master/lib/Crypto/Random/_UserFriendlyRNG.py
  """

  def __init__(self, seed):
    self.closed = False
    self.DRBG = hmac_drbg.HMAC_DRBG(hashlib.sha512(seed).digest())

  def close(self):
    self.closed = True

  def flush(self):
    pass

  def read(self, N):
    """Return N bytes from the RNG."""
    if self.closed:
      raise ValueError("I/O operation on closed file")
    if not isinstance(N, (long, int)):
      raise TypeError("an integer is required")
    if N < 0:
      raise ValueError("cannot read to end of infinite stream")

    # we don't care about the reseed counter.  We're completely deterministic, no new randomness to inject
    self.DRBG.reseed_counter = 1

    # Create the "random" data
    return self.DRBG.generate(N)


