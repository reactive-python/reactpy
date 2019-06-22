Installation
============

How to install iDOM.


Stable Version
--------------

iDOM is on PyPI_ so all you need to do is use pip_:

.. code-block:: bash

    pip install idom


Development Version
-------------------

In order to work with iDOM's source code you'll to install:

+ Yarn_

+ `Git Bash`_ (to run shell scripts on Windows)

The source code for iDOM is hosted on GitHub so you'll need git_ to download it:

.. code-block:: bash

    git clone https://github.com/rmorshea/idom.git
    cd idom

At this point you should be able to run this install command to:

- Install an editable version of the Python code

- Transpile the Javascript and copy it to ``src/py/idom/static``

- Install some pre-commit hooks for Git

.. code-block:: bash

    pip install -e . -r requirements/dev.txt && pre-commit install

Any time you modify a Javascript client library and want it to be served directly from
``idom.server`` you'll need to transpile the Javascript again and copy it to the
``src/py/idom/static`` folder. Don't worry though, you can do this by simply
re-install iDOM via ``pip``:

.. code-block:: bash

    pip install -e .




.. Links
.. =====

.. _git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
.. _Git Bash: https://gitforwindows.org/
.. _PyPI: https://pypi.org/
.. _pip: https://pypi.org/project/pip/
.. _Yarn: https://yarnpkg.com/lang/en/docs/install
