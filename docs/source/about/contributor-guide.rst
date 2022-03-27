Contributor Guide
=================

.. note::

    The
    `Code of Conduct <https://github.com/idom-team/idom/blob/main/CODE_OF_CONDUCT.md>`__
    applies in all community spaces. If you are not familiar with our Code of Conduct
    policy, take a minute to read it before making your first contribution.

The IDOM team welcomes contributions and contributors of all kinds - whether they come
as code changes, participation in the discussions, opening issues and pointing out bugs,
or simply sharing your work with your colleagues and friends. We're excited to see how
you can help move this project and community forward!


.. _everyone can contribute:

Everyone Can Contribute!
------------------------

Trust us, there's so many ways to support the project. We're always looking for people
who can:

- Improve our documentation
- Teach and tell others about IDOM
- Share ideas for new features
- Report bugs
- Participate in general discussions

Still aren't sure what you have to offer? Just :discussion-type:`ask us <question>` and
we'll help you make your first contribution.


.. note::

    If you have any questions during set up or development post on our
    :discussion-type:`discussion board <question>` and we'll answer them.


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

Creating a Changelog Entry
..........................

As part of your pull request, you'll want to edit the `Changelog
<https://github.com/idom-team/idom/blob/main/docs/source/about/changelog.rst>`__ by
adding an entry describing what you've changed or improved. You should write an entry in
the style of `Keep a Changelog <https://keepachangelog.com/>`__ that falls under one of
the following categories, and add it to the :ref:`Unreleased` section of the changelog:

- **Added** - for new features.
- **Changed** - for changes in existing functionality.
- **Deprecated** - for soon-to-be removed features.
- **Removed** - for now removed features.
- **Fixed** - for any bug fixes.
- **Documented** - for improvements to this documentation.
- **Security** - in case of vulnerabilities.

If one of the sections doesn't exist, add it. If it does already, add a bullet point
under the relevant section. Here's a short example of what an unreleased changelog entry
might look like:

.. code-block:: rst

    Unreleased
    ----------

    **Added**

    - A really cool new feature - :pull:`123`

    **Changed**

    - The behavior of some existing feature - :pull:`456`

    **Fixed**

    - Some really bad bug - :issue:`789`

.. note::

    ``:issue:`` and ``:pull:`` refer to issue and pull request ticket numbers.


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

The test suite for IDOM is executed with Nox_. The suite covers:

1. Server-side Python code with PyTest_

2. The end-to-end application using Selenium_ in Python

3. Client-side Javascript code with UVU_

To run the full suite of tests you'll need to install:

- `Google Chrome`_

- ChromeDriver_.

.. warning::

    Be sure the version of `Google Chrome`_ and ChromeDriver_ you install are compatible.

Once you've installed the aforementioned browser and web driver you'll be able to run:

.. code-block:: bash

    nox -s test

If you prefer to run the tests using a headless browser:

.. code-block:: bash

    nox -s test -- --headless


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
- Prettier_ - a tool for automatically formatting various file types

The most strict measure of quality enforced on the codebase is 100% test coverage in
Python files. This means that every line of coded added to IDOM requires a test case
that exercises it. This doesn't prevent all bugs, but it should ensure that we catch the
most common ones.

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

To build and display the documentation locally run:

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
installed Docker, you can run:

.. code-block:: bash

    nox -s docs_in_docker

Where you can then navigate to http://localhost:5000..


Release Process
---------------

Creating a release for IDOM involves two steps:

1. Tagging a version
2. Publishing a release

To **tag a version** you'll run the following command:

.. code-block:: bash

    nox -s tag -- <the-new-version>

Which will update the version for:

- Python packages
- Javascript packages
- The changelog

You'll be then prompted to confirm the auto-generated updates before those changes will
be staged, committed, and pushed along with a new tag matching ``<the-new-version>``
which was specified earlier.

Lastly, to **publish a release** `create one in GitHub
<https://docs.github.com/en/github/administering-a-repository/releasing-projects-on-github/managing-releases-in-a-repository>`__.
Because we pushed a tag using the command above, there should already be a saved tag you
can target when authoring the release. The release needs a title and description. The
title should simply be the version (same as the tag), and the description should simply
use GitHub's "Auto-generated release notes".


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
