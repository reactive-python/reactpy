# ReactPy's Documentation

We provide two main ways to run the docs. Both use
[`nox`](https://pypi.org/project/nox/):

- `nox -s docs` - displays the docs and rebuilds when files are modified.
- `nox -s docs-in-docker` - builds a docker image and runs the docs from there.

If any changes to the core of the documentation are made (i.e. to non-`*.rst` files),
then you should run a manual test of the documentation using the `docs_in_docker`
session.

If you wish to build and run the docs by hand you need to perform two commands, each
being run from the root of the repository:

- `sphinx-build -b html docs/source docs/build`
- `python scripts/run_docs.py`

The first command constructs the static HTML and any Javascript. The latter actually
runs the web server that serves the content.
