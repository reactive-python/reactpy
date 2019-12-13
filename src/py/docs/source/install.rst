Installation
============

IDOM is on PyPI_ so all you need to do is use pip_ to install a **stable** version:

.. code-block:: bash

    pip install idom[stable]

To setup up all extra features:

.. code-block:: bash

    # all extra features
    pip install idom[all]

.. note::

    To install *specific* features see :ref:`Extra Features`

To get a **pre-release**:

.. code-block:: bash

    pip install idom --pre

.. note::

    Pre-releases may be unstable or subject to change

.. contents::
  :local:
  :depth: 1


Development Version
-------------------

In order to work with IDOM's source code you'll need to install:

- git_

- Yarn_

You'll begin by copy the source from GitHub onto your computer using Git:

.. code-block:: bash

    git clone https://github.com/rmorshea/idom.git
    cd idom

At this point you should be able to run this install command to:

- Install an editable version of the Python code

- Transpile the Javascript and copy it to ``src/py/idom/static``

- Install some pre-commit hooks for Git

.. code-block:: bash

    pip install -e . -r requirements.txt && pre-commit install

If you modify a Javascript library you'll need to re-run this command:

.. code-block:: bash

    pip install -e .

This will transpile the Javascript again and copy it to the
``src/py/idom/static`` folder.


Running The Test
----------------

The test suite for IDOM covers:

1. Server-side Python code using PyTest_

2. The end-to-end application using Selenium_

3. (Coming soon...) Client side Javascript code

To run the full suite of tests you'll need to install:

- `Google Chrome`_

- ChromeDriver_.

.. warning::

    Be sure the version of `Google Chrome`_ and ChromeDriver_ you install are compatible.

Once you've installed the aforementined browser and web driver you should be able to
run:

.. code-block:: bash

    pytest src/py/tests

If you prefer to run the tests using a headless browser:

.. code-block:: bash

    pytest src/py/tests --headless

.. Links
.. =====

.. _Google Chrome: https://www.google.com/chrome/
.. _ChromeDriver: https://chromedriver.chromium.org/downloads
.. _git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
.. _Git Bash: https://gitforwindows.org/
.. _PyPI: https://pypi.org/project/idom
.. _pip: https://pypi.org/project/pip/
.. _PyTest: pytest <https://docs.pytest.org
.. _Selenium: https://www.seleniumhq.org/
.. _Yarn: https://yarnpkg.com/lang/en/docs/install
