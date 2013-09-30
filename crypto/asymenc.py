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

        private = ''
        self.no_private = True
        if isinstance(self.key.private, str):
            private = self.key.private
            self.no_private = False
        self.ecc = ECC(public=self.key.public, 
                       private=private,
                       curve=self.key.curve)

    def encrypt(self, data):
        if self.no_private:
            raise Exception("Encryption requires a private key")
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
        if self.no_private:
            raise Exception("Signing requires a private key")
        signature = self.ecc.sign(data)
        return base64.b64encode(signature)
    def verify(self, data, signature):
        return self.ecc.verify(data, base64.b64decode(signature))
