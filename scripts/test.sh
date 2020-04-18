#!/bin/bash
set -e

pytest src/tests --headless --cov=idom --cov-fail-under=82 --reruns 1
black --verbose --check src/py
flake8 src/
mypy src/idom
sphinx-build -b html src/docs/source src/docs/build
