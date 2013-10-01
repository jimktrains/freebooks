from dulwich.repo import Repo
from dulwich.server import FileSystemBackend, TCPGitServer
import threading

backend = FileSystemBackend().open_repository("test-remote/.git")
dul_server = TCPGitServer(backend, 'localhost', 55828)
dul_server.serve()

