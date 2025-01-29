from __future__ import annotations

import socket
import sys
from contextlib import closing


def find_available_port(host: str, port_min: int = 8000, port_max: int = 9000) -> int:
    """Get a port that's available for the given host and port range"""
    for port in range(port_min, port_max):
        with closing(socket.socket()) as sock:
            try:
                if sys.platform in ("linux", "darwin"):
                    # Fixes bug on Unix-like systems where every time you restart the
                    # server you'll get a different port on Linux. This cannot be set
                    # on Windows otherwise address will always be reused.
                    # Ref: https://stackoverflow.com/a/19247688/3159288
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((host, port))
            except OSError:
                pass
            else:
                return port
    msg = f"Host {host!r} has no available port in range {port_max}-{port_max}"
    raise RuntimeError(msg)
