# IDOM's Documentation

We provide two main ways to run the docs. Both use `nox` which has a `noxfile.py` at the
root of the repository. Running the docs with `nox -s docs` will start up an iteractive
session which will rebuild the docs any time a file is modified. Using `nox -s
docs_in_docker` on the other hand, will build a docker image and run the docs from
there. The latter command mimics how the docs will behave in production. As such, if any
changes to the core of the documentation are made (i.e. to non-`*.rst` files), then you
should run a manual test of the documentation using the `docs_in_docker` session.

If you with to build and run the docs by hand you need to perform two commands, each
being run from the root of the repository:

- `sphinx-build -b html docs/source docs/build`
- `python scripts/run_docs.py`

The first command constructs the static HTML and any Javascript. The latter actually
runs the web server that serves the content.
