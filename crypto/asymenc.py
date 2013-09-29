from pyecc import ECC
from asymencdata import ASymEncData
from encresult import EncResult
import base64
class ASymEnc:
    def __init__(self, key = None):
        if key is None:
            self.key = ASymKey()
        else:
            self.key = key

        self.ecc = ECC(public=self.key.public, 
                       private=self.key.private, 
                       curve=self.key.curve)

    def encrypt(self, data):
        encrypted = self.ecc.encrypt(data)
        encrypted = ASymEncData(self.key.curve, encrypted)
        encrypted = EncResult(encrypted, self.key.hmac_key)
        return encrypted
    def decrypt(self, data):
        decrypted = EncResult(data, self.key.hmac_key)
        if decrypted.verify(): 
            decrypted = self.ecc.decrypt(data.enc_data.data)
            return decrypted
        else:
            raise Exception('HMAC invalid')
    def sign(self, data):
        signature = self.ecc.sign(data)
        return base64.b64encode(signature)
    def verify(self, data, signature):
        return self.ecc.verify(data, base64.b64decode(signature))
