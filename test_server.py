from dulwich.repo import Repo
from dulwich.server import DictBackend, TCPGitServer
import threading
repo = Repo("test-remote")
backend = DictBackend({'/': repo})
dul_server = TCPGitServer(backend, 'localhost', 55828)
dul_server.serve()
