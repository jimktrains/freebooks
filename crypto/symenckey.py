from Crypto.Cipher import AES
from Crypto import Random
from crypto.symenc import SymEnc
BLOCK_SIZE = 32
class SymEncKey:
    def __init__(self, enc = None, hmac = None, algo = None, 
                 mode = None, block_size = None):
        if enc is None:
            self.algo = "AES"
            self.mode = AES.MODE_CBC
            self.block_size = BLOCK_SIZE
            self.encrypt = Random.get_random_bytes(self.block_size)
            self.hmac = Random.get_random_bytes(self.block_size)
        elif isinstance(enc, dict):
            self.encrypt = enc['encrypt']
            self.hmac = enc['hmac']
            self.algo = enc['algo']
            self.mode = enc['mode']
            self.block_size = enc['block_size']
        else:
            self.encrypt = enc
            self.hmac = hmac
            self.algo = "AES" # So, these are an is for now
            self.mode = AES.MODE_CBC 
            self.block_size = block_size
            
    def to_dict(self, pickle_key):
        s = SymEnc(pickle_key)
        return {
            'algo': self.algo,
            'mode': self.mode, 
            'block_size': self.block_size,
            'encrypt': s.encrypt(self.encrypt).to_dict(),
            'hmac': s.encrypt(self.hmac).to_dict()
        }

    @staticmethod
    def from_dict(pickle_key, state):
        s = SymEnc(pickle_key)
        state['encrypt'] = s.decrypt(EncResult.from_dict(state['encrypt']))
        state['hmac'] = s.decrypt(EncResult.from_dict(state['hmac']))
        return SymEncKey(state)
