Contributor Guide
=================

.. note::

    If you have any questions during set up or development post on our
    :discussion-type:`discussion board <question>` and we'll answer them.

This project uses the `GitHub Flow`_ (more detail :ref:`below <Making a Pull Request>`)
for collaboration and consists primarily of Python code and Javascript code. A
:ref:`variety of tools <Development Environment>` are used to aid in its development.
Any code contributed to IDOM is validated by a :ref:`series of tests <Running The
Tests>` to ensure its quality and correctness.


Making a Pull Request
---------------------

To make your first code contribution to IDOM, you'll need to install Git_ (or
`Git Bash`_ on Windows). Thankfully there are many helpful
`tutorials <https://github.com/firstcontributions/first-contributions/blob/master/README.md>`__
about how to get started. To make a change to IDOM you'll do the following:

`Fork IDOM <https://docs.github.com/en/github/getting-started-with-github/fork-a-repo>`__:
    Go to `this URL <https://github.com/idom-team/idom>`__ and click the "Fork" button.

`Clone your fork <https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository>`__:
    You use a ``git clone`` command to copy the code from GitHub to your computer.

`Create a new branch <https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging>`__:
    You'll ``git checkout -b your-first-branch`` to create a new space to start your work

:ref:`Prepare your Development Environment <Development Environment>`:
    We explain in more detail below how to install all IDOM's dependencies

`Push your changes <https://docs.github.com/en/github/using-git/pushing-commits-to-a-remote-repository>`__:
    Once you've made changes to IDOM, you'll ``git push`` them to your fork.

`Create a Pull Request <https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request>`__:
    We'll review your changes, run some :ref:`tests <Running The Tests>` and
    :ref:`equality checks <Code Quality Checks>` and, with any luck, accept your request.
    At that point your contribution will be merged into the main codebase!


Development Environment
-----------------------

In order to develop IDOM locally you'll first need to install the following:

.. list-table::
    :header-rows: 1

    *   - What to Install
        - How to Install

    *   - Git_
        - https://git-scm.com/book/en/v2/Getting-Started-Installing-Git

    *   - Python >= 3.7
        - https://realpython.com/installing-python/

    *   - NodeJS >= 14
        - https://nodejs.org/en/download/package-manager/

    *   - NPM >= 7.13
        - https://docs.npmjs.com/try-the-latest-stable-version-of-npm

    *   - Docker
        - https://docs.docker.com/get-docker/

.. note::

    NodeJS distributes a version of NPM, but you'll want to get the latest

Once done, you can clone a local copy of this repository:

.. code-block:: bash

    git clone https://github.com/idom-team/idom.git
    cd idom

Then, you should be able to run the command below to:

- Install an editable version of the Python code

- Download, build, and install Javascript dependencies

- Install some pre-commit_ hooks for Git

.. code-block:: bash

    pip install -e . -r requirements.txt && pre-commit install

If you modify any Javascript, you'll need to re-install IDOM:

.. code-block:: bash

    pip install -e .

However you may also ``cd`` to the ``src/client`` directory which contains a
``package.json`` that you can use to run standard ``npm`` commands from.


Running The Tests
-----------------

The test suite for IDOM uses Nox_ and NPM_ in order to validate:

1. Server-side Python code with PyTest_

2. The end-to-end application using Selenium_ in Python

3. Client-side Javascript code with UVU_


Running Python Tests
....................

To run the full suite of Python tests you'll need to install:

- `Google Chrome`_

- ChromeDriver_.

.. warning::

    Be sure the version of `Google Chrome`_ and ChromeDriver_ you install are compatible.

Once you've installed the aforementioned browser and web driver you should be able to
run:

.. code-block:: bash

    nox -s test

If you prefer to run the tests using a headless browser:

.. code-block:: bash

    nox -s test -- --headless

You can pass other options to pytest in a similar manner:

.. code-block:: bash

    nox -s test -- arg --flag --key=value


Running Javascript Tests
........................

If you've already run ``npm install`` inside the ``src/idom/client/app`` directory, you
can execute the suite of workspace tests under ``packages/*`` with:

.. code-block::

    npm test

As a final check, you might want to run ``npm run build``. This command is run in the
top-level ``setup.py`` installation script for the Python package, so if this command
fails, the installation of the Python package with ``pip`` will too.


Code Quality Checks
-------------------

Several tools are run on the codebase to help validate its quality. For the most part,
if you set up your :ref:`Development Environment` with pre-commit_ to check your work
before you commit it, then you'll be notified when changes need to be made or, in the
best case, changes will be made automatically for you.

The following are currently being used:

- MyPy_ - a static type checker
- Black_ - an opinionated code formatter
- Flake8_ - a style guide enforcement tool
- ISort_ - a utility for alphabetically sorting imports
- Prettier_ - a tool for autimatically formatting Javascript code

The most strict measure of quality enforced on the codebase is 100% coverage. This means
that every line of coded added to IDOM requires a test case that exercises it. This
doesn't prevent all bugs, but it should ensure that we catch the most common ones.

If you need help understanding why code you've submitted does not pass these checks,
then be sure to ask, either in the :discussion-type:`Community Forum <question>` or in
your :ref:`Pull Request <Making a Pull Request>`.

.. note::

    You can manually run ``nox -s format`` to auto format your code without having to
    do so via ``pre-commit``. However, many IDEs have ways to automatically format upon
    saving a file
    (e.g.`VSCode <https://code.visualstudio.com/docs/python/editing#_formatting>`__)


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

.. code-block:: bash

    nox -s test_docs

Building the documentation as it's deployed in production requires Docker_. Once you've
installed, you can run:

.. code-block:: bash

    nox -s docs_in_docker

You should then navigate to  to see the documentation.


Release Process
---------------

1. Update version
2. Add changelog entry

   - Include merged pull requests
   - Include closed issues

3. Commit final release changes
4. Create a release tag
5. Manually author a release in GitHub


Update Release Version
......................

To update the version for all core Javascript and Python packages in IDOM run:

.. code-block:: bash

    nox -s update_version -- <new-version>

.. note::

    The new version must adhere to `SemVer <https://semver.org/>`__. Once IDOM
    becomes stable we will shift to using `CalVer <https://calver.org/>`__.


Create Changelog Entry
......................

Immediately after updating the version you'll need to create a changelog entry for the
release. This should **always** include a human authored summary of the changes it
includes. For example, new or deprecated features, performance improvements, and bug
fixes (whatever is relevant). To help with this, there are some useful tools for
gathering the Pull Requests and Issues that have been merged and resolved since the last
release. While reviewing these items can help in writing a human authored release
summary, you **must not** resort to a bullet list of Pull Request and Issue
descriptions. Putting these two together, the format of a changelog entry should look a
bit like this:

.. code-block:: text

    X.Y.Z
    -----

    The release summary...

    **Closed Issues**

    - Some issue - :issue:`123`
    - Another issue - :issue:`456`

    **Pull Requests**

    - Some pull request - :pull:`123`
    - Another pull request - :pull:`456`

    **Deprecated Features**

    - Description one
    - Description two

To create the list of pull requests and closed issues you can copy the output of the
following commands using the ``<format>`` of your choosing (``rst``, ``md``, ``text``):

.. note::

    You should currate the list - not everything needs to be included.

.. code-block:: bash

    nox -s latest_closed_issues -- <format>
    nox -s latest_pull_requests -- <format>

Once the version has been updated and the changelog entry completed, you should commit
the changes.


Creating The Release
....................

The final release process involves two steps:

1. Creating a tag for the release
2. Authoring a release in GitHub

To create the release tag you can run the following command:

.. note::

    To just create the tag without pushing, omit the trailing ``push`` argument

.. code-block:: bash

    nox -s tag -- push

Last, you must create a
`"Release" <https://docs.github.com/en/github/administering-a-repository/releasing-projects-on-github/managing-releases-in-a-repository>`__
in GitHub. Because we pushed a tag using the command above, there should already be a
saved draft which needs a title and desription. The title should simply be the version
(same as the tag), and the description should, at minimum, be a markdown version of the
already authored :ref:`Changelog summary <Create Changelog Entry>`.


Other Core Repositories
-----------------------

IDOM depends on, or is used by several other core projects. For documentation on them
you should refer to their respective documentation in the links below:

- `idom-react-component-cookiecutter
  <https://github.com/idom-team/idom-react-component-cookiecutter>`__ - Template repo
  for making :ref:`Custom Javascript Components`.
- `flake8-idom-hooks <https://github.com/idom-team/flake8-idom-hooks>`__ - Enforces the
  :ref:`Rules of Hooks`
- `idom-jupyter <https://github.com/idom-team/idom-jupyter>`__ - IDOM integration for
  Jupyter
- `idom-dash <https://github.com/idom-team/idom-dash>`__ - IDOM integration for Plotly
  Dash
- `django-idom <https://github.com/idom-team/django-idom>`__ - IDOM integration for
  Django

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
.. _MyPy: http://mypy-lang.org/
.. _Black: https://github.com/psf/black
.. _Flake8: https://flake8.pycqa.org/en/latest/
.. _ISort: https://pycqa.github.io/isort/
.. _UVU: https://github.com/lukeed/uvu
.. _Prettier: https://prettier.io/
