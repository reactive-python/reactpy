#!/bin/bash
set -e

cd idom/client
rm -rf node_modules
rm -rf web_modules
rm -rf etc_modules
npm install
npm run snowpack
cd ../../
