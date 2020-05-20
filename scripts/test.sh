#!/bin/bash
set -e

pytest --headless
black . --check --exclude "idom/client/static/node_modules/.*"
flake8 idom
mypy --strict idom
sphinx-build -b html docs/source docs/build
