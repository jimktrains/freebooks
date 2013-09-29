from dulwich.repo import *
from dulwich.objects import *
import yaml
import os
import argparse
import math
import shutil
import time

# Man is this ugly
from crypto.asymencdata import ASymEncData
from crypto.asymenc import ASymEnc
from crypto.asymkey import ASymKey
from crypto.encresult import EncResult
from crypto.symencdata import SymEncData
from crypto.symenckey import SymEncKey
from crypto.symencpasswordkey import SymEncPasswordKey
from crypto.symenc import SymEnc




parser = argparse.ArgumentParser(description='Process the ledger')
parser.add_argument('--ledger', '-l', metavar="DIR", type=str,
                   help='Path to the ledger', required=True)
parser.add_argument('--initialize', "-i", action='store_true',
                   help='Initialize the ledger. Must be used with --add-user', 
                   default=False)
parser.add_argument('--add-user', "-a", metavar="USER_NAME", type=str,
                   help='Adds a user')
args = parser.parse_args()

print args


def add_user(username):
    if not os.path.exists(args.ledger + '/users/'):
        os.makedirs(args.ledger + '/users/')
    if os.path.exists(args.ledger + '/users/' + args.add_user):
        raise Exception("User %s exists. Cannot regenerate key" % username)
    print "Generating User Key"
    user_passwd = SymEncPasswordKey()
    user_key = ASymKey()

    to_store = {
        'key_key': user_passwd.to_dict(),
        'key': user_key.to_dict(user_passwd)
    }
    user_key_yaml = yaml.dump(to_store, default_flow_style = False)

    with open(args.ledger + '/users/' + args.add_user, 'w+') as key_file:
        key_file.write(user_key_yaml)
    return user_key

def create_master_key():
    if os.path.exists(args.ledger + '/key'):
        raise Exception('key exists. Cannot regenerate key')
    print "Generating key"
    key_key = SymEncPasswordKey()

    key = SymEncKey()

    to_store = {
        'key_key': key_key.to_dict(),
        'key': key.to_dict(key_key)
    }
    key_yaml = yaml.dump(to_store, default_flow_style=False)
    with open(args.ledger + '/key', 'w+') as key_file:
        key_file.write(key_yaml)

def add_files_and_sign(repo, repo_base, files,username, user_key):
    ase = ASymEnc(user_key)

    object_store = repo.object_store

    t = Tree()
    for fn in files:
        b = None
        with open(repo_base + "/" + fn, 'r') as f:
            b = Blob.from_string(f.read())
        t.add(fn, 0100644, b.id)
        object_store.add_object(b)
    object_store.add_object(t)
    sig = ase.sign(t.sha().hexdigest())

    commit = Commit()
    commit.tree = t.id
    commit.author = commit.committer = username
    commit.commit_time = commit.author_time = int(time.time())
    tz = parse_timezone('-0400')[0] # Should be fixed
    commit.commit_timezone = commit.author_timezone = tz
    commit.encoding = "UTF-8"
    commit.message = sig

    object_store.add_object(commit)

    repo.refs['refs/heads/master'] = commit.id

if args.initialize:
    if not args.add_user:
        raise Exception("Must specifiy a user when initializing")

    # FOR TESTING ONLY
    # THIS WILL ERROR
    if os.path.exists(args.ledger):
        shutil.rmtree(args.ledger)

    ledger_repo = Repo.init(args.ledger, mkdir=True)

    create_master_key()
    user_key = add_user(args.add_user)

    add_files_and_sign(ledger_repo, args.ledger,
            ['key', 'users/' + args.add_user], 
            args.add_user, user_key)
    #ledger_repo.do_commit("Init", committer=args.add_user)
    #print ledger_repo.head()


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
