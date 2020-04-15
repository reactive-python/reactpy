#!/bin/bash
cd src/idom/client
rm -rf node_modules
rm -rf web_modules
npm install
npm run snowpack
cd ../../../
