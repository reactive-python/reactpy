#!/bin/bash
set -e

pytest src/py/tests --headless --cov=idom --cov-fail-under=79
black --verbose --check src/py
flake8 src/py
mypy src/py/idom --config-file=src/py/mypy.ini
