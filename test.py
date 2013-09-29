from fs.zipfs import ZipFS
from Crypto import Random
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto.Hash import HMAC
from Crypto.Hash import SHA256

import base64

import uuid 
import time
import math
import binascii
import getpass
import yaml
import os
from pyecc import ECC


BLOCK_SIZE = 32

BS = BLOCK_SIZE
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[0:-ord(s[-1])]

def gen_iv():
    # Version 1 is based on:
    #  * Counter
    #  * Time
    #  * MAC Address
    # Shouldn't repeat, even across machines
    # and under most normal conditions
    uuid1 = str(uuid.uuid1()).replace('-','')
    iv = binascii.unhexlify(uuid1)
    return iv

def encrypt(data,key):
    enc_key = key[0]
    hmac_key = key[1]

    iv = gen_iv()

    cipher = AES.new(enc_key, AES.MODE_CBC, iv)
    enc_data = cipher.encrypt(pad(data))
    
    iv   = base64.b64encode(iv)
    enc_data = base64.b64encode(enc_data)

    key_combo = { "iv": iv, 
                  "encrypted": enc_data,
                  "algo": "AES",
                  "mode": "CBC",
                  "keylen": BLOCK_SIZE
                }

    h = HMAC.new(hmac_key, digestmod = SHA256)
    serial = "%s:%s:%s:%s:%s" % ("AES", "CBC", BLOCK_SIZE, iv, enc_data)
    h.update(serial)
    hmac = base64.b64encode(h.digest())

    hmac_combo = {
                    "hmac": hmac,
                    "algo": "SHA256"
                 }

    enc_yaml = {
        "encrypted": key_combo,
        "hmac": hmac_combo
    }

    return enc_yaml

def decrypt(enc, key):
    enc_key = key[0]
    hmac_key = key[1]

    iv = enc['encrypted']['iv']
    data = enc['encrypted']['encrypted']
    serial = "%s:%s:%s:%s:%s" % ("AES", "CBC", BLOCK_SIZE, iv, data)

    h = HMAC.new(hmac_key, digestmod = SHA256)
    h.update(serial)
    hmac = base64.b64encode(h.digest())

    iv = base64.b64decode(enc['encrypted']['iv'])
    # Why I don't have to pad is beyond me
    data = base64.b64decode(enc['encrypted']['encrypted'])

    if hmac == enc['hmac']['hmac']:
        # So yeah....We're just going to assume it's AES-CBC
        cipher = AES.new(enc_key, AES.MODE_CBC, iv) 
        raw_data = unpad(cipher.decrypt(data))
        return raw_data
    else:
        raise Exception("Bad Password")

def password_to_key(enc_salt = None,
                    hmac_salt = None, 
                    max_len = 8, 
                    confirm = False):
    if enc_salt is None:
        enc_salt = Random.get_random_bytes(32)
    if hmac_salt is None:
        hmac_salt = Random.get_random_bytes(32)

    passwd = ''
    cpasswd = '-'
    while cpasswd != passwd:
        while len(passwd) < max_len:
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

    enc_key = PBKDF2(passwd, enc_salt, BLOCK_SIZE)
    hmac_key = PBKDF2(passwd, hmac_salt, BLOCK_SIZE)

    return ((enc_key, hmac_key), (enc_salt, hmac_salt))

raw_key = None

if not os.path.exists('key'): 

    print "Generating key"
    key_key, passwd_salt  = password_to_key(confirm = True)
    raw_key = []
    raw_key.append(base64.b64encode(Random.get_random_bytes(32)))
    raw_key.append(base64.b64encode(Random.get_random_bytes(32)))
    print raw_key
    raw_key = ":".join(raw_key)
    key = encrypt(raw_key, key_key)
    key['password_salts'] = {
        "key": base64.b64encode(passwd_salt[0]),
        "hmac": base64.b64encode(passwd_salt[1])
    }
    key_yaml = yaml.dump( key, default_flow_style=False)

    with open('key', 'w+') as key_file:
        key_file.write(key_yaml)
else:
    print "Reading key"
    enc_key = None
    with open('key', 'r') as key_file:
        enc_key = key_file.read()
    enc_key = yaml.load(enc_key)

    password_salt = enc_key['password_salts']
    enc_salt = base64.b64decode(password_salt['key'])
    hmac_salt = base64.b64decode(password_salt['hmac'])
    key_key, passwd_salt = password_to_key(enc_salt=enc_salt, 
                                           hmac_salt=hmac_salt)

    raw_key = decrypt(enc_key, key_key).split(':')
    raw_key[0] = base64.b64decode(raw_key[0])
    raw_key[1] = base64.b64decode(raw_key[1])
