from socket import socket
from typing import cast


def find_available_port(host: str) -> int:
    """Get a port that's available for the given host"""
    sock = socket()
    sock.bind((host, 0))
    return cast(int, sock.getsockname()[1])
