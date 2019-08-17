#!/usr/bin/env bash

set -e

cd src

# install JS dependencies
cd js

yarn --ignore-engines
yarn setup

cd ../

# clean up possible old install
if [ -d "py/idom/static" ]; then
  rm -rf py/idom/static
fi
mkdir py/idom/static

# build js packages
cd js
npm run build
cd ../

# copy built files to py
cp -r js/packages/idom-jupyter-widget-hook/build py/idom/static/jupyter-widget
cp -r js/packages/idom-simple-client/build py/idom/static/simple-client

cd ../

cd ../
