from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto import Random
import base64
import getpass
BLOCK_SIZE = 32
class SymEncPasswordKey:
    def __init__(self, enc = None, hmac = None, algo = None, 
                 mode = None, block_size = None):
        passwd = None
        if enc is None:
            self.algo = "AES"
            self.mode = AES.MODE_CBC
            self.block_size = BLOCK_SIZE
            self.encrypt_salt = Random.get_random_bytes(self.block_size)
            self.hmac_salt = Random.get_random_bytes(self.block_size)
            passwd = SymEncPasswordKey.get_password(confirm = True)
        elif isinstance(enc, dict):
            self.encrypt_salt = enc['encrypt_salt']
            self.hmac_salt = enc['hmac_salt']
            self.algo = enc['algo']
            self.mode = enc['mode']
            self.block_size = enc['block_size']
            passwd = SymEncPasswordKey.get_password()
        else:
            self.encrypt_salt = enc
            self.hmac_salt = hmac
            self.algo = "AES" # So, these are an is for now
            self.mode = AES.MODE_CBC 
            self.block_size = block_size
            passwd = SymEncPasswordKey.get_password()
        self.encrypt = PBKDF2(passwd, self.encrypt_salt, BLOCK_SIZE)
        self.hmac = PBKDF2(passwd, self.hmac_salt, BLOCK_SIZE)
    @staticmethod
    def get_password(max_len = 8, confirm = False):
        return "jimkjimk"
        passwd = ''
        cpasswd = '-'
        while cpasswd != passwd:
            passwd = getpass.getpass("Please enter the password: ")
            if confirm:
                if len(passwd) < max_len:
                    print "Password needs to be at least %d characters" % max_len
                    cpasswd = passwd + "BAD"
                else:
                    cpasswd = getpass.getpass("Please confirm the password: ")
                    if passwd != cpasswd:
                        print "Passwords do not match"
            else:
                cpasswd = passwd
        return passwd

    def to_dict(self):
        return {
            'algo': self.algo,
            'mode': self.mode, 
            'block_size': self.block_size,
            'encrypt_salt': base64.b64encode(self.encrypt_salt),
            'hmac_salt': base64.b64encode(self.hmac_salt)
        }

    @staticmethod
    def from_dict(state):
        state['encrypt_salt'] = base64.b64decode(state['encrypt_salt'])
        state['hmac_salt'] = base64.b64decode(state['hmac_salt'])
        return SymEncPasswordKey(state)
