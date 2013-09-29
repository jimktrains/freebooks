from Crypto.Hash import SHA256
from Crypto.Hash import HMAC
import base64
class EncResult:
    def __init__(self, enc_data, hmac_key):
        if isinstance(enc_data, EncResult):
            self.enc_data = enc_data.enc_data
            self.hmac_data = enc_data.hmac_data
            self.hmac_key = hmac_key
        else:
            self.enc_data = enc_data
            self.hmac_key = hmac_key

            h = HMAC.new(self.hmac_key, digestmod = SHA256)
            h.update(str(self.enc_data))
            self.hmac_data = base64.b64encode(h.digest())
    def verify(self):
        h = HMAC.new(self.hmac_key, digestmod = SHA256)
        h.update(str(self.enc_data))
        hmac_data = base64.b64encode(h.digest())
        
        return hmac_data == self.hmac_data
    def to_dict(self):
        return {
            "data": self.enc_data.to_dict(),
            "hmac": self.hmac_data
        }

    @staticmethod
    def from_dict(pickle_key, state):
        return EncResult(state['data'], state['hmac'])
