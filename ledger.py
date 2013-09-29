from dulwich.repo import *
from dulwich.objects import *
import yaml
import os
import argparse
import shutil
import time
import datetime
from dateutil.tz import tzlocal

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

    @staticmethod
    def init(path, user):
        Repo.init(path, mkdir=True)
        user.generate_key()
        ledger = Ledger(path, user)
        ledger.actions.append('Init')
        ledger.create_master_key()
        ledger.add_user(user)
        ledger.commit()
        
    def commit(self):
        if self.current_user is None:
            raise Exception('No User Logged in')
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
