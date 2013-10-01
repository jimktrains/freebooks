from dulwich.repo import *
from dulwich.objects import *
import yaml
import os
import argparse
import shutil
import time
import datetime
from dateutil.tz import tzlocal
import uuid
from user import User
import hashlib

# Man is this ugly
from crypto.asymencdata import ASymEncData
from crypto.asymenc import ASymEnc
from crypto.asymkey import ASymKey
from crypto.encresult import EncResult
from crypto.symencdata import SymEncData
from crypto.symenckey import SymEncKey
from crypto.symencpasswordkey import SymEncPasswordKey
from crypto.symenc import SymEnc

class LedgerException(Exception):
    pass

class Ledger:
    def __init__(self, path, user = None):
        self.path = path
        self.repo = Repo(path)
        self.current_user = user
        self.dirty_files = []
        self.actions = []
        self.key = None
        self.cached_users = None
        self.cached_txs = None

    def __enter__(self):
        self.load_all_users()
        if isinstance(self.current_user, str):
            self.auth_user(self.current_user)
        errs = self.errors()
        if errs:
            raise LedgerException(errs)
        self.load_key()
        return self
    def __exit__(self, type, value, traceback):
        if value is None:
            return True
        return False
    @staticmethod
    def init(path, user):
        Repo.init(path, mkdir=True)
        user.generate_key()
        ledger = Ledger(path, user)
        ledger.actions.append('Init')
        ledger.create_master_key()
        ledger.add_user(user)
        

    @staticmethod
    def str_to_sign(ctime, parent, digest, actions, user):
        if isinstance(parent, list):
            parent = ",".join(parent)
        action_digest =  hashlib.sha256(actions).hexdigest()
        return "%d:%s:%s:%s:%s" % (ctime, parent, digest, action_digest, user)
    def commit(self, branch, actions, data=None):
        if self.current_user is None:
            raise LedgerException('No User Logged in')
        branch = "refs/heads/%s" % branch
        parent = ''
        if branch in self.repo.refs:
            parent = [self.repo.refs[branch]]

        digest = hashlib.sha256(data).hexdigest()
        ctime = int(time.time())
        if isinstance(actions, list):
            actions = ". ".join(actions)

        s2s = Ledger.str_to_sign(ctime = ctime, 
                                 parent = parent, 
                                 digest = digest, 
                                 actions = actions,
                                 user = repr(self.current_user))
        ase = ASymEnc(self.current_user.key)
        sig = ase.sign(s2s)
        if not ase.verify(s2s, sig):
            raise Exception('Bah!')
        
        msg = "Actions: %s\nSig: %s\n%s" % (actions, sig, data)

        commit = Commit()
        commit.author = commit.committer = repr(self.current_user)
        tzo = int(tzlocal().utcoffset(datetime.datetime.now()).total_seconds())
        commit.commit_timezone = commit.author_timezone = tzo
        commit.commit_time = commit.author_time = ctime
        commit.encoding = "UTF-8"
        commit.message = msg
        # SHA of an empty tree
        # git hash-object -t tree /dev/null
        commit.tree = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'

        if parent:
            commit.parents = parent

        object_store = self.repo.object_store
        object_store.add_object(commit)

        self.repo.refs[branch] = commit.id

    def load_key(self):
        for key in self.keys():
            key_key = key['key_key']
            key_key = SymEncPasswordKey.from_dict(key_key)
            key = key['key']
            key = SymEncKey.from_dict(key_key, key)
            self.key = key
            break # There should only be a single key, or we'll just use the first one

    def check_key(self):
        if self.key is None:
            self.load_key()
            if self.key is None:
                raise LedgerException("Key not loaded")

    def auth_user(self, username):
        if username not in self.cached_users:
            raise LedgerException("User %s doesn't exist" % username)
        user = self.cached_users[username]
        user.decrypt_key()
        self.current_user = user

    def add_user(self, user):
        user_key_yaml = yaml.dump(user.to_dict(), default_flow_style = False)
        self.commit('users', "Create user %s" % user, data=user_key_yaml)

    def create_master_key(self):
        key_key = SymEncPasswordKey()

        key = SymEncKey()

        to_store = {
            'key_key': key_key.to_dict(),
            'key': key.to_dict(key_key)
        }

        key_yaml = yaml.dump(to_store, default_flow_style=False)
        self.commit('key', "Generated Master Key", data=key_yaml)
        self.key = key

    def create_tx(self, from_account, to_account, description, amount):
        self.check_key()

        encor = SymEnc(self.key)
        description = encor.encrypt(description)
        amount = encor.encrypt(str(amount))

        tx = {
            'description': description.to_dict(),
            'amount': amount.to_dict(),
            'to_account': to_account,
            'from_account': from_account,
        }

        tx_yaml = yaml.dump(tx, default_flow_style = False)
        self.commit('txs',"Added Tx", data=tx_yaml)

    def walk_branch(self, branch, verify = True):
        branch = "refs/heads/%s" % branch
        if branch not in self.repo.refs:
             return
        for tx in self.repo.get_walker(include=self.repo.refs[branch]):
            a = tx.commit.message.split('\n', 2)
            actions = a[0]
            sig = a[1]
            data = a[2]
            actions = actions.split(':')[1].strip()
            sig = sig.split(':')[1].strip()
            s2s = Ledger.str_to_sign(ctime = tx.commit.commit_time, 
                                     parent = ','.join(tx.commit.parents),
                                     digest = hashlib.sha256(data).hexdigest(), 
                                     actions = actions,
                                     user = tx.commit.author)
            if verify:
                user = self.cached_users[tx.commit.author]
                asc = ASymEnc(user.key)
                if not asc.verify(s2s, sig):
                    raise LedgerException("Commit %s has a bad sig" % tx.commit.id)
            if data is None and -1 != tx.commit.message.find('Merge'):
                continue
            yield data, tx.commit
    def keys(self): # There should only ever be 1, but...
        for data, commit in self.walk_branch('key'):
            key = yaml.safe_load(data)
            yield key    
    def txs(self):
        self.check_key()
        if self.cached_txs is not None:
            for tx in self.cached_txs:
                yield tx
        else:
            self.cached_txs = []
            encor = SymEnc(self.key)
            for data, commit in self.walk_branch('txs'):
                tx = yaml.safe_load(data)
                tx['who'] = commit.author
                tx['when'] = commit.commit_time
                tx['amount'] = int(encor.decrypt(EncResult.from_dict(tx['amount'])))
                tx['description'] = encor.decrypt(EncResult.from_dict(tx['description']))
                self.cached_txs.append(tx)
                yield tx
    def users(self, verify = True):
        for data, commit in self.walk_branch('users', verify=verify):
            data = yaml.safe_load(data)
            user = User.from_dict_auth(data, decrypt = False)
            yield user
    def load_all_users(self):
        users = {}
        if self.cached_users is not None:
            return None
        for user in self.users(verify=False):
            users[repr(user)] = user
            users[str(user)] = user
        self.cached_users = users
    def balances(self):
        accts = {}
        self.check_key()
        for tx in self.txs():
            from_account = tx['from_account']
            to_account = tx['to_account']
            amount = tx['amount']
            if from_account not in accts:
                accts[from_account] = 0
            if to_account not in accts:
                accts[to_account] = 0
            accts[from_account] -= amount
            accts[to_account] += amount
        return accts

    def verify(self):
        return self.errors() is None
    def errors(self):
        try:
            for tx in self.txs(): pass
            for tx in self.users(): pass
            for tx in self.keys(): pass
        except LedgerException as e:
            return str(e)
        return None
    def txs_for_account(self, account):
        for tx in self.txs():
            if account == tx['to_account'] or account == tx['from_account']:
                yield tx
