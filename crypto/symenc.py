from Crypto.Cipher import AES
from Crypto import Random
from symencdata import SymEncData
from encresult import EncResult
BLOCK_SIZE = 32
class SymEnc:
    def __init__(self, key):
        self.key = key
    def gen_iv(self):
        return Random.get_random_bytes(16) # Why isn't this the block size?

    # Why do I need self here
    @staticmethod
    def pad(s):
        pad_len = (BLOCK_SIZE - len(s) % BLOCK_SIZE)
        pad_char = chr(pad_len)
        s = s + (pad_char * pad_len)
        return s
    @staticmethod
    def unpad(s):
         return s[0:-ord(s[-1])]
    def encrypt(self, data):
        iv = self.gen_iv()
        cipher = AES.new(self.key.encrypt, self.key.mode, iv)
        enc_data = cipher.encrypt(SymEnc.pad(data))
        enc_data = SymEncData(self.key.algo, self.key.mode, 
                              self.key.block_size, iv, enc_data)
        enc_data = EncResult(enc_data, self.key.hmac)
        return enc_data

    def decrypt(self, data):
        # Should make sure the data and the key
        # are the same mode and all...or not store the
        # mode in the key?
        if data.verify():
            cipher = AES.new(self.key.encrypt, 
                             data.enc_data.mode, 
                             data.enc_data.iv) 
            raw_data = SymEnc.unpad(cipher.decrypt(data.enc_data.data))
            return raw_data
        else:
            raise Exception("Bad Password")
