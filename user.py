# Man is this ugly
from crypto.asymencdata import ASymEncData
from crypto.asymenc import ASymEnc
from crypto.asymkey import ASymKey
from crypto.encresult import EncResult
from crypto.symencdata import SymEncData
from crypto.symenckey import SymEncKey
from crypto.symencpasswordkey import SymEncPasswordKey
from crypto.symenc import SymEnc
class User:
    def __init__(self, username, full_name, email):
        self.username = username
        self.full_name = full_name
        self.email = email
    def generate_key(self):
        self.password = SymEncPasswordKey()
        self.key = ASymKey()
    def to_dict(self):
        return {
            'password': self.password.to_dict(),
            'key': self.key.to_dict(self.password),
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email
        }
    @staticmethod
    def from_dict_auth(state):
        user = User(state['username'], state['full_name'], state['email'])
        user.password = SymEncPasswordKey.from_dict(state['password'])
        user.key = ASymKey.from_dict(user.password, state['key'])
        return user 
    def __str__(self):
        return self.username
    def __repr__(self):
        return "%s <%s>" % (self.full_name, self.email)
