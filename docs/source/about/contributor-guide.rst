Contributor Guide
=================

Creating a development environment
----------------------------------

If you plan to make code changes to this repository, you will need to install the following dependencies first:

- `Git <https://www.python.org/downloads/>`__
- `Python 3.9+ <https://www.python.org/downloads/>`__
- `Hatch <https://hatch.pypa.io/latest/>`__
- `Bun <https://bun.sh/>`__
- `Docker <https://docs.docker.com/get-docker/>`__ (optional)

Once you finish installing these dependencies, you can clone this repository:

.. code-block:: bash

    git clone https://github.com/reactive-python/reactpy.git
    cd reactpy

Executing test environment commands
-----------------------------------

By utilizing ``hatch``, the following commands are available to manage the development environment.

Python Tests
............

.. list-table::
    :header-rows: 1

    *   - Command
        - Description
    *   - ``hatch test``
        - Run Python tests using the current environment's Python version
    *   - ``hatch test --all``
        - Run tests using all compatible Python versions
    *   - ``hatch test --python 3.9``
        - Run tests using a specific Python version
    *   - ``hatch test -k test_use_connection``
        - Run only a specific test

Python Package
..............

.. list-table::
    :header-rows: 1

    *   - Command
        - Description
    *   - ``hatch fmt``
        - Run all linters and formatters
    *   - ``hatch fmt --check``
        - Run all linters and formatters, but do not save fixes to the disk
    *   - ``hatch fmt --linter``
        - Run only linters
    *   - ``hatch fmt --formatter``
        - Run only formatters
    *   - ``hatch run python:type_check``
        - Run the Python type checker

JavaScript Packages
...................

.. list-table::
    :header-rows: 1

    *   - Command
        - Description
    *   - ``hatch run javascript:check``
        - Run the JavaScript linter/formatter
    *   - ``hatch run javascript:fix``
        - Run the JavaScript linter/formatter and write fixes to disk
    *   - ``hatch run javascript:test``
        - Run the JavaScript tests
    *   - ``hatch run javascript:build``
        - Build all JavaScript packages
    *   - ``hatch run javascript:build_event_to_object``
        - Build the ``event-to-object`` package
    *   - ``hatch run javascript:build_client``
        - Build the ``@reactpy/client`` package
    *   - ``hatch run javascript:build_app``
        - Build the ``@reactpy/app`` package

Documentation
.............

.. list-table::
    :header-rows: 1

    *   - Command
        - Description
    *   - ``hatch run docs:serve``
        - Start the documentation preview webserver
    *   - ``hatch run docs:build``
        - Build the documentation
    *   - ``hatch run docs:check``
        - Check the documentation for build errors
    *   - ``hatch run docs:docker_serve``
        - Start the documentation preview webserver using Docker
    *   - ``hatch run docs:docker_build``
        - Build the documentation using Docker

Environment Management
......................

.. list-table::
    :header-rows: 1

    *   - Command
        - Description
    *   - ``hatch build --clean``
        - Build the package from source
    *   - ``hatch env prune``
        - Delete all virtual environments created by ``hatch``
    *   - ``hatch python install 3.12``
        - Install a specific Python version to your system

Other ReactPy Repositories
--------------------------

ReactPy has several external packages that can be installed to enhance your user experience. For documentation on them
you should refer to their respective documentation in the links below:

- `reactpy-router <https://github.com/reactive-python/reactpy-router>`__ - ReactPy support for URL
  routing
- `reactpy-js-component-template
  <https://github.com/reactive-python/reactpy-js-component-template>`__ - Template repo
  for making :ref:`Custom Javascript Components`.
- `reactpy-django <https://github.com/reactive-python/reactpy-django>`__ - ReactPy integration for
  Django
- `reactpy-jupyter <https://github.com/reactive-python/reactpy-jupyter>`__ - ReactPy integration for
  Jupyter

.. Links
.. =====

.. _Hatch: https://hatch.pypa.io/
.. _Invoke: https://www.pyinvoke.org/
.. _Google Chrome: https://www.google.com/chrome/
.. _Docker: https://docs.docker.com/get-docker/
.. _Git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
.. _Git Bash: https://gitforwindows.org/
.. _NPM: https://www.npmjs.com/get-npm
.. _PyPI: https://pypi.org/project/reactpy
.. _pip: https://pypi.org/project/pip/
.. _PyTest: pytest <https://docs.pytest.org
.. _Playwright: https://playwright.dev/python/
.. _React: https://reactjs.org/
.. _Heroku: https://www.heroku.com/what
.. _GitHub Actions: https://github.com/features/actions
.. _pre-commit: https://pre-commit.com/
.. _GitHub Flow: https://guides.github.com/introduction/flow/
.. _MyPy: http://mypy-lang.org/
.. _Black: https://github.com/psf/black
.. _Flake8: https://flake8.pycqa.org/en/latest/
.. _Ruff: https://github.com/charliermarsh/ruff
.. _UVU: https://github.com/lukeed/uvu
.. _Prettier: https://prettier.io/
.. _ESLint: https://eslint.org/
