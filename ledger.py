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

# Man is this ugly
from crypto.asymencdata import ASymEncData
from crypto.asymenc import ASymEnc
from crypto.asymkey import ASymKey
from crypto.encresult import EncResult
from crypto.symencdata import SymEncData
from crypto.symenckey import SymEncKey
from crypto.symencpasswordkey import SymEncPasswordKey
from crypto.symenc import SymEnc
class Ledger:
    def __init__(self, path, user = None):
        self.path = path
        self.repo = Repo(path)
        self.current_user = user
        self.dirty_files = []
        self.actions = []
        self.key = None

    @staticmethod
    def init(path, user):
        Repo.init(path, mkdir=True)
        user.generate_key()
        ledger = Ledger(path, user)
        ledger.actions.append('Init')
        ledger.create_master_key()
        ledger.add_user(user)
        ledger.init_tx_dir()
        ledger.commit()
        
    def commit(self):
        if self.current_user is None:
            raise Exception('No User Logged in')
        if 0 == len(self.dirty_files):
            return None;
        ase = ASymEnc(self.current_user.key)

        object_store = self.repo.object_store

        t = Tree()
        for fn in self.dirty_files:
            b = None
            with open(self.path + "/" + fn, 'r') as f:
                b = Blob.from_string(f.read())
            t.add(fn, 0100644, b.id)
            object_store.add_object(b)
        object_store.add_object(t)

        actions = ". ".join(self.actions)

        parent = None
        if 'refs/heads/master' in self.repo.refs:
            parent = self.repo.refs['refs/heads/master']
        
        ctime = int(time.time())
        str_to_sign = "%d:%s:%s:%s" % (ctime, parent, t.sha().hexdigest(), str(self.current_user))
        sig = ase.sign(str_to_sign)

        message = "Actions: %s\nSig: %s" % (actions, sig)

        commit = Commit()
        commit.tree = t.id
        commit.author = commit.committer = repr(self.current_user)
        tzo = int(tzlocal().utcoffset(datetime.datetime.now()).total_seconds())
        commit.commit_timezone = commit.author_timezone = tzo
        commit.commit_time = commit.author_time = ctime
        commit.encoding = "UTF-8"
        commit.message = message

        if parent:
            commit.parents = [parent]

        object_store.add_object(commit)

        self.repo.refs['refs/heads/master'] = commit.id

        self.dirty_files = []
        self.actions = []

    def load_key(self):
        key = None
        with open(self.path + '/key', 'r') as key_file: 
            key = yaml.safe_load(key_file.read())
        key_key = key['key_key']
        key_key = SymEncPasswordKey.from_dict(key_key)
        key = key['key']
        key = SymEncKey.from_dict(key_key, key)
        self.key = key

    def check_key(self):
        if self.key is None:
            raise Exception("Key not loaded")

    def init_tx_dir(self):
        if not os.path.exists(self.path + '/tx/'):
            os.makedirs(self.path + '/tx/')
        with open(self.path + '/tx/.placeholder', 'w') as f:
            f.write('');
        self.dirty_files.append('tx/.placeholder')
        self.actions.append('Create Tx dir')

    def add_user(self, user):
        if not os.path.exists(self.path + '/users/'):
            os.makedirs(self.path + '/users/')
        user_path = self.path + '/users/' + str(user)
        if os.path.exists(user_path):
            raise Exception("User %s exists. Cannot regenerate key" % str(user))
        user_key_yaml = yaml.dump(user.to_dict(), default_flow_style = False)

        with open(user_path, 'w+') as key_file:
            key_file.write(user_key_yaml)
            self.dirty_files.append('users/' + str(user))
        self.actions.append("Create user %s" % user)

    def create_master_key(self):
        if os.path.exists(self.path + '/key'):
            raise Exception('key exists. Cannot regenerate key')
        print "Generating key"
        key_key = SymEncPasswordKey()

        key = SymEncKey()

        to_store = {
            'key_key': key_key.to_dict(),
            'key': key.to_dict(key_key)
        }
        key_yaml = yaml.dump(to_store, default_flow_style=False)
        with open(self.path + '/key', 'w+') as key_file:
            key_file.write(key_yaml)
            self.dirty_files.append('key')
        self.actions.append("Generated Master Key")

    def auth_user(self, username):
        if not os.path.exists(self.path + "/users/" + username):
            raise Exception("%s doesn't exist" % username)
        with open(self.path + "/users/" + username, 'r') as f:
            user_dict = yaml.safe_load(f.read())
        user = User.from_dict_auth(user_dict)
        self.current_user = user

    @staticmethod
    def new_id():
        return str(uuid.uuid1())

    def id_to_path(self, i):
        id_parts = i.split('-')
        # 0        1    2    3    4
        # 3870ed38-29e1-11e3-be97-001de0794fc3
        dir_path =  "tx/" + id_parts[4] + "/" + id_parts[3] + \
                    "/" + id_parts[2]
        file_name = id_parts[1] + "-" + id_parts[0]
        return dir_path + "/" + file_name, dir_path
    def create_tx(self, from_account, to_account, description, amount):
        self.check_key()

        encor = SymEnc(self.key)
        tx_id = Ledger.new_id()
        description = encor.encrypt(description)
        amount = encor.encrypt(str(amount))

        tx = {
            'id': tx_id,
            'description': description.to_dict(),
            'amount': amount.to_dict(),
            'to_account': to_account,
            'from_account': from_account,
        }

        tx_yaml = yaml.dump(tx, default_flow_style = False)
        fn,dirn = self.id_to_path(tx_id)
        os.makedirs(self.path + "/" + dirn)
        with open(self.path + "/" + fn, "w") as f:
            f.write(tx_yaml)
        self.dirty_files.append(fn)
        self.actions.append('Added Tx ' + tx_id)

    def list_tx(self, root = None):
        txs = []
        if root is None:
            root = self.path + "/tx"
        for root, subFolders, files in os.walk(root):
            for folder in subFolders:
                txs = txs + self.list_tx(folder)
            for filename in files:
                if filename != '.placeholder':
                    filePath = os.path.join(root, filename)
                    txs.append(self.read_tx_file(filePath))
        return txs
            
    def read_tx_id(self, tx_id):
        fn = self.id_to_path(tx_id)
        return self.read_tx_file(fn)
    def read_tx_file(self, tx_file):
        self.check_key()
        encor = SymEnc(self.key)
        tx = None
        with open(tx_file, 'r') as f:
            tx = yaml.safe_load(f.read())
        tx['description'] = encor.decrypt(EncResult.from_dict(tx['description']))
        tx['amount'] = encor.decrypt(EncResult.from_dict(tx['amount']))
        return tx
    def balances(self):
        txs = self.list_tx()
        accts = {}
        for tx in txs:
            from_account = tx['from_account']
            to_account = tx['to_account']
            amount = int(tx['amount'])
            if from_account not in accts:
                accts[from_account] = 0
            if to_account not in accts:
                accts[to_account] = 0
            accts[from_account] -= amount
            accts[to_account] += amount
        return accts

    def verify(self):
        for rev in self.repo.get_walker():
            print rev
