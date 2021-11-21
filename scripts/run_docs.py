import os
import sys


# all scripts should be run from the repository root so we need to insert cwd to path
# to import docs
sys.path.insert(0, os.getcwd())


if __name__ == "__main__":
    from docs import run

    run()
