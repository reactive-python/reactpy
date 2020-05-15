#!/bin/bash
set -e

pytest --headless -vv
black . --check --exclude idom/client/node_modules/.*
flake8 idom
mypy --strict idom
sphinx-build -b html docs/source docs/build
