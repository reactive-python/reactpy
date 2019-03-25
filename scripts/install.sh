set -e

# Javascript
# ==========

cd src/js

yarn
yarn setup

cd ../../

# Python
# ======

cd src/py

poetry install

cd ../../
