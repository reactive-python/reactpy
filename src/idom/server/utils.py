from contextlib import closing
from importlib import import_module
from socket import socket
from typing import Any, List, Type


def find_builtin_server_type(type_name: str) -> Type[Any]:
    """Find first installed server implementation"""
    supported_packages = ["sanic", "flask", "tornado"]

    installed_builtins: List[str] = []
    for name in supported_packages:
        try:
            import_module(name)
        except ImportError:  # pragma: no cover
            continue
        else:
            builtin_module = import_module(f"idom.server.{name}")
            installed_builtins.append(builtin_module.__name__)
        try:
            return getattr(builtin_module, type_name)  # type: ignore
        except AttributeError:  # pragma: no cover
            pass
    else:  # pragma: no cover
        if not installed_builtins:
            raise RuntimeError(
                f"Found none of the following builtin server implementations {supported_packages}"
            )
        else:
            raise ImportError(
                f"No server type {type_name!r} found in installed implementations {installed_builtins}"
            )


def find_available_port(host: str, port_min: int = 8000, port_max: int = 9000) -> int:
    """Get a port that's available for the given host and port range"""
    for port in range(port_min, port_max):
        with closing(socket()) as sock:
            try:
                sock.bind((host, port))
            except OSError:
                pass
            else:
                return port
    raise RuntimeError(
        f"Host {host!r} has no available port in range {port_max}-{port_max}"
    )
