from pyecc import ECC
from Crypto.Hash import SHA256
import base64
from symenc import SymEnc
from encresult import EncResult
class ASymKey:
    def __init__(self, key = None):
        if key is None:
            self.ecc = ECC.generate()
            self.public = self.ecc._public
            self.private = self.ecc._private
            self.curve = self.ecc._curve
        else:
            self.public = key['public']
            self.private = key['private']
            self.curve = key['curve']
        self.hmac_key = None
        if isinstance(self.private, str):
            h = SHA256.new()
            h.update(self.private)
            self.hmac_key = h.digest()

    def to_dict(self, pickle_key):
        s = SymEnc(pickle_key)

        return {
            "public": base64.b64encode(self.public),
            "private": s.encrypt(self.private).to_dict(),
            "curve": self.curve,
        }

    # These ares should be reversed so that state is req
    @staticmethod
    def from_dict(pickle_key = None, state = None):
        key = {
            "public": base64.b64decode(state['public']),
            "private": EncResult.from_dict(state['private']),
            "curve": state['curve'],
        }
        if pickle_key is not None:
            s = SymEnc(pickle_key)
            key['private'] = s.decrypt(key['private'])

        return ASymKey(key)
