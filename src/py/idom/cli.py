# type: ignore
"""IDOM

Custom install configuration options

Usage:
  idom codec [register | deregister | registered]
"""
import os
from distutils.sysconfig import get_python_lib

import idom
from docopt import docopt


_PTH_FILE = os.path.join(get_python_lib(), "idom.pth")


def main():
    arguments = docopt(__doc__, version=idom.__version__)
    if arguments["codec"]:
        _codec(arguments)


def _codec(arguments):
    if arguments["register"]:
        if os.path.exists(_PTH_FILE):
            print(f"already registered: '{_PTH_FILE}")
        else:
            with open(_PTH_FILE, "w+") as f:
                f.write("import idom.codec.register\n")
    elif arguments["deregister"]:
        if not os.path.exists(_PTH_FILE):
            print(f"already deregister: '{_PTH_FILE}")
        else:
            os.remove(_PTH_FILE)
    elif arguments["registered"]:
        print(os.path.exists(_PTH_FILE))
    elif arguments["location"]:
        print(_PTH_FILE)


if __name__ == "__main__":
    main()
