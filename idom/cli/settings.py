import os
from typing import List

NAMES: List[str] = []

IDOM_CLI_SHOW_SPINNER = True
IDOM_CLI_SHOW_OUTPUT = True
IDOM_CLI_DEBUG = False


_to_str = {
    bool: lambda x: str(int(x)),
    str: lambda x: x,
    list: lambda x: ",".join(x),
}

_from_str = {
    bool: lambda x: bool(int(x)),
    str: lambda x: x,
    list: lambda x: x.split(","),
}


def _load_from_environ():
    gs = globals()
    for k, v in globals().items():
        if k.startswith("IDOM_"):
            v_type = type(v)
            default = _to_str[v_type](v)
            gs[k] = _from_str[v_type](os.environ.setdefault(k, default))
            NAMES.append(k)


_load_from_environ()
