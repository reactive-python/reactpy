#!/bin/bash
pytest src/py/tests --headless
black --verbose --check src/py
flake8 src/py
mypy src/py/idom --config-file=src/py/mypy.ini
