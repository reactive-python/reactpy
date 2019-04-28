Install
=======

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

At this point you should be able to run an install script:

.. code-block:: bash

    pip install -e . -r requirements/dev.txt

Any time you modify a Javascript client library and want it to be served directly from
``idom.server`` you'll need to re-run this script to build your changes and copy them
into the expected static file folder within ``src/py/idom/static``.


.. Links
.. =====

.. _git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
.. _Git Bash: https://gitforwindows.org/
.. _PyPI: https://pypi.org/
.. _pip: https://pypi.org/project/pip/
.. _Yarn: https://yarnpkg.com/lang/en/docs/install
