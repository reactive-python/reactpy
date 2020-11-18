import os
from typing import List

NAMES: List[str] = []

IDOM_CLI_SHOW_SPINNER = True
IDOM_CLI_SHOW_OUTPUT = True
IDOM_CLI_DEBUG = False


def _load_from_environ():
    gs = globals()
    for k, v in globals().items():
        if k.startswith("IDOM_"):
            if isinstance(v, bool):
                gs[k] = bool(int(os.environ.setdefault(k, str(int(v)))))
            else:
                gs[k] = os.environ.setdefault(k, v)
            NAMES.append(k)


_load_from_environ()
