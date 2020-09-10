set -e
idom install victory semantic-ui-react @material-ui/core
sphinx-build -b html docs/source docs/build
cd docs
python -c "import main; main.local()"
cd ../
