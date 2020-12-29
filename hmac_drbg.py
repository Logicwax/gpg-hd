import hashlib
import hmac

class DRBG(object):
    def __init__(self, seed):
        self.key = b'\x00' * 32
        self.val = b'\x01' * 32
        self.reseed(seed)

    def hmac(self, key, val):
        return hmac.new(key, val, hashlib.sha256).digest()

    def reseed(self, data=b''):
        self.key = self.hmac(self.key, self.val + b'\x00' + data)
        self.val = self.hmac(self.key, self.val)

        if data:
            self.key = self.hmac(self.key, self.val + b'\x01' + data)
            self.val = self.hmac(self.key, self.val)

    def generate(self, n):
        temp = b''
        while len(temp) < n:
            self.val = self.hmac(self.key, self.val)
            temp += self.val

        self.reseed()

        return temp[:n]