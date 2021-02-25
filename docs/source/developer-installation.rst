Developer Installation
======================

In order to work with IDOM's source code you'll need to install:

- git_

- npm_

You'll begin by copying the source from GitHub onto your computer using Git:

.. code-block:: bash

    git clone https://github.com/rmorshea/idom.git
    cd idom

At this point you should be able to run the command below to:

- Install an editable version of the Python code

- Download, build, and install Javascript dependencies

- Install some pre-commit hooks for Git

.. code-block:: bash

    pip install -e . -r requirements.txt && pre-commit install

Since we're using native ES modules for our Javascript, you should usually be able to
refresh your browser page to see your latest changes to the client. However if you
modify any dependencies you can run standard ``npm`` commands to install them or
simply run the following to re-evaluate the ``package.json``:

.. code-block:: bash

    pip install -e .


Running The Tests
-----------------

The test suite for IDOM is executed using Nox_ and covers:

1. Server-side Python code with PyTest_

2. The end-to-end application using Selenium_

3. (`Coming soon <https://github.com/idom-team/idom/issues/195>`_) Client side Javascript code

To run the full suite of tests you'll need to install:

- `Google Chrome`_

- ChromeDriver_.

.. warning::

    Be sure the version of `Google Chrome`_ and ChromeDriver_ you install are compatible.

Once you've installed the aforementined browser and web driver you should be able to
run:

.. code-block:: bash

    nox

If you prefer to run the tests using a headless browser:

.. code-block:: bash

    HEADLESS=1 nox


Building The Documentation
--------------------------

Building the documentation as it's deployed in production requires Docker_. Once you've
installed ``docker`` you'll need to build and then run a container with the service:

.. code-block:: bash

    docker build . --file docs/Dockerfile --tag idom-docs:latest
    docker run -it -p 5000:5000 -e DEBUG=true --rm idom-docs:latest

You should then navigate to http://127.0.0.1:5000 to see the documentation.


.. Links
.. =====

.. _Google Chrome: https://www.google.com/chrome/
.. _ChromeDriver: https://chromedriver.chromium.org/downloads
.. _Docker: https://docs.docker.com/get-docker/
.. _git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
.. _Git Bash: https://gitforwindows.org/
.. _npm: https://www.npmjs.com/get-npm
.. _PyPI: https://pypi.org/project/idom
.. _pip: https://pypi.org/project/pip/
.. _PyTest: pytest <https://docs.pytest.org
.. _Selenium: https://www.seleniumhq.org/
.. _Nox: https://nox.thea.codes/en/stable/#
