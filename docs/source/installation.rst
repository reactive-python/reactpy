Installation
============

To install IDOM and a default implementation for all features:

.. code-block:: bash

    pip install idom[stable]

For a minimal installation that lacks implementations for some features:

.. code-block:: bash

    pip install idom

For more installation options see the :ref:`Extra Features` section.

.. note::

    IDOM also supplies a :ref:`Flake8 Plugin` to help enforce the :ref:`Rules of Hooks`


Extra Features
--------------

Optionally installable features of IDOM. To include, them use the given "Name" from the
table below:

.. code-block:: bash

    pip install idom[NAME]

.. list-table::
    :header-rows: 1
    :widths: 1 3

    *   - Name
        - Description

    *   - ``stable``
        - Default implementations for all IDOM's features

    *   - ``testing``
        - Utilities for testing IDOM using `Selenium <https://www.selenium.dev/>`__

    *   - ``sanic``
        - `Sanic <https://sanicframework.org/>`__ as a :ref:`Layout Server`

    *   - ``fastapi``
        - `FastAPI <https://fastapi.tiangolo.com//>`__ as a :ref:`Layout Server`

    *   - ``tornado``
        - `Tornado <https://www.tornadoweb.org/en/stable/>`__ as a :ref:`Layout Server`

    *   - ``flask``
        - `Flask <https://palletsprojects.com/p/flask/>`__ as a :ref:`Layout Server`

    *   - ``all``
        - All the features listed above (not usually needed)
