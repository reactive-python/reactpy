Installation
============

iDOM is on PyPI_ so all you need to do is use pip_:

.. code-block:: bash

    pip install idom


Development Version
-------------------

In order to work with iDOM's source code you'll need to install:

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


.. Links
.. =====

.. _git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
.. _Git Bash: https://gitforwindows.org/
.. _PyPI: https://pypi.org/project/idom
.. _pip: https://pypi.org/project/pip/
.. _Yarn: https://yarnpkg.com/lang/en/docs/install
