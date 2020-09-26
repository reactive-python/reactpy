set -e
python scripts/install_doc_js_modules.py
sphinx-build -E -b html docs/source docs/build
cd docs
python -c "import main; main.local('$1')"
cd ../
