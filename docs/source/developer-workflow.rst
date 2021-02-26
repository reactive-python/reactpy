Developer Workflow
==================

This project uses the `GitHub Flow`_ for collaboration and consists primarilly of Python
code and Javascript code. A variety of tools are used to aid in its development. Below
is a short list of the tools which will be most commonly referenced in the sections to
follow:

.. list-table::
    :header-rows: 1

    *   - Tool
        - Used For

    *   - Git_
        - version control

    *   - Nox_
        - automating development tasks.

    *   - PyTest_
        - executing the Python-based test suite

    *   - pre-commit_
        - helping impose basic syle guidelines

    *   - NPM_
        - managing and installing Javascript packages

    *   - Selenium_ and ChromeDriver_
        - to control the browser while testing

    *   - `GitHub Actions`_
        - hosting and running our CI/CD suite

    *   - Docker_ and Heroku_
        - containerizing and hosting this documentation


Development Environment
-----------------------

In order to work with IDOM's source code you'll need to install Git_ (or `Git Bash`_ on
Windows). Once done you can clone a local copy of this repository:

.. code-block:: bash

    git clone https://github.com/rmorshea/idom.git
    cd idom

At this point you should be able to run the command below to:

- Install an editable version of the Python code

- Download, build, and install Javascript dependencies

- Install some pre-commit hooks for Git

.. code-block:: bash

    pip install -e . -r requirements.txt && pre-commit install

If you modify any Javascript, you'll need to re-install IDOM:

.. code-block:: bash

    pip install -e .

However you may also ``cd`` to the ``idom/client/app`` directory which contains a
``package.json`` that you can use to run standard ``npm`` commands from.


Running The Tests
-----------------

The test suite for IDOM is executed using Nox_ and covers:

1. Server-side Python code with PyTest_

2. The end-to-end application using Selenium_

To run the full suite of tests you'll need to install:

- `Google Chrome`_

- ChromeDriver_.

.. warning::

    Be sure the version of `Google Chrome`_ and ChromeDriver_ you install are compatible.

Once you've installed the aforementined browser and web driver you should be able to
run:

.. code-block:: bash

    nox -s test

If you prefer to run the tests using a headless browser:

.. code-block:: bash

    nox -s test -- pytest[--headless]


Code Style
----------

Under construction... in the meantime though, we use
`Black <https://github.com/psf/black>` to format our code.


Building The Documentation
--------------------------

To build and display the documentation simply run:

.. code-block:: bash

    nox -s docs

This will compile the documentation from its source files into HTML, start a web server,
and open a browser to display the now generated documentation. Whenever you change any
source files the web server will automatically rebuild the documentation and refresh the
page. Under the hood this is using
`sphinx-autobuild <https://github.com/executablebooks/sphinx-autobuild>`__.

To run some of the examples in the documentation as if they were tests run:

.. code-block::

    nox -s test_docs

Building the documentation as it's deployed in production requires Docker_. Once you've
installed, you can run:

.. code-block:: bash

    nox -s docs_in_docker

You should then navigate to  to see the documentation.


Making a Pull Request
---------------------

Under construction...


Release Process
---------------

Under construction...


How It's Published to PyPI
..........................

Under construction...


How Docs are Deployed to Heroku
...............................

Under construction...


Other Core Repositories
-----------------------

IDOM involves several other core projects. For documentation on them you should refer to
their respective documentation in the links below

- https://github.com/idom-team/idom-client-react - Javascript client for IDOM
- https://github.com/idom-team/flake8-idom-hooks - Enforces the :ref:`Rules of Hooks`


.. Links
.. =====

.. _Google Chrome: https://www.google.com/chrome/
.. _ChromeDriver: https://chromedriver.chromium.org/downloads
.. _Docker: https://docs.docker.com/get-docker/
.. _Git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
.. _Git Bash: https://gitforwindows.org/
.. _NPM: https://www.npmjs.com/get-npm
.. _PyPI: https://pypi.org/project/idom
.. _pip: https://pypi.org/project/pip/
.. _PyTest: pytest <https://docs.pytest.org
.. _Selenium: https://www.seleniumhq.org/
.. _Nox: https://nox.thea.codes/en/stable/#
.. _React: https://reactjs.org/
.. _Heroku: https://www.heroku.com/what
.. _GitHub Actions: https://github.com/features/actions
.. _pre-commit: https://pre-commit.com/
.. _GitHub Flow: https://guides.github.com/introduction/flow/
