set -e
sphinx-build -b html docs/source docs/build
cd docs
python -c "import main; main.local()"
cd ../
