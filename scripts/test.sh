#!/bin/bash
set -e

pytest --headless

echo ""
echo "Black"
echo "====="
black . --check --exclude "idom/client/static/node_modules/.*"

echo ""
echo "Flake8"
echo "======"
flake8 idom tests docs && echo "No issues 🎉"

echo ""
echo "MyPy"
echo "===="
mypy --strict idom

echo ""
echo "Sphinx"
echo "======"
sphinx-build -b html docs/source docs/build
