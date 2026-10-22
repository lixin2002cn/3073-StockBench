"""A process-local guard for the offline starter (not a security sandbox)."""
from contextlib import contextmanager
from unittest.mock import patch


class NetworkDisabledError(RuntimeError):
    pass


@contextmanager
def no_network(enabled=True):
    """Block Python socket connections, including local model servers."""
    if not enabled:
        yield
        return

    def blocked(*args, **kwargs):
        raise NetworkDisabledError("Network access is disabled for this run.")

    with patch("socket.socket.connect", blocked), patch("socket.socket.connect_ex", blocked), patch("socket.create_connection", blocked), patch("socket.getaddrinfo", blocked), patch("socket.socket.sendto", blocked):
        yield
