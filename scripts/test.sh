#!/bin/bash
set -e

pytest src/py/tests --headless --cov=idom --cov-fail-under=82
black --verbose --check src/py
flake8 src/py
mypy src/py/idom
sphinx-build -b html src/py/docs/source src/py/docs/build
