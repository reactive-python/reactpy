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

    To contribute to IDOM, refer to the :ref:`Developer Workflow` instructions.


Extra Features
--------------

Optionally installable features of IDOM. To install them use the given "Name" from the table below

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

    *   - ``tornado``
        - `Tornado <https://www.tornadoweb.org/en/stable/>`__ as a :ref:`Layout Server`

    *   - ``flask``
        - `Flask <https://palletsprojects.com/p/flask/>`__ as a :ref:`Layout Server`

    *   - ``dialect``
        - :ref:`Python Language Extension` for writing JSX-like syntax

    *   - ``all``
        - All the features listed above (not usually needed)


Python Language Extension
-------------------------

IDOM includes an import-time transpiler for writing JSX-like syntax in a ``.py`` file!

.. code-block:: python

    # dialect=html
    from idom import html

    message = "hello world!"
    attrs = {"height": "10px", "width": "10px"}
    model = html(f"<div ...{attrs}><p>{message}</p></div>")

    assert model == {
        "tagName": "div",
        "attributes": {"height": "10px", "width": "10px"},
        "children": [{"tagName": "p", "children": ["hello world!"]}],
    }

With Jupyter and IPython support:

.. code-block:: python

    %%dialect html
    from idom import html
    assert html(f"<div/>") == {"tagName": "div"}

That you can install with ``pip``:

.. code-block::

    pip install idom[dialect]


Usage
.....

1. Import ``idom`` in your application's ``entrypoint.py``

2. Import ``your_module.py`` with a ``# dialect=html`` header comment.

3. Inside ``your_module.py`` import ``html`` from ``idom``

4. Run ``python entrypoint.py`` from your console.

So here's the files you should have set up:

.. code-block:: text

    project
    |-  entrypoint.py
    |-  your_module.py

The contents of ``entrypoint.py`` should contain:

.. code-block::

    import idom  # this needs to be first!
    import your_module

While ``your_module.py`` should contain the following:

.. code-block::

    # dialect=html
    from idom import html
    assert html(f"<div/>") == {"tagName": "div"}

And that's it!


How It Works
............

Once ``idom`` has been imported at your application's entrypoint, any following modules
imported with a ``# dialect=html`` header comment get transpiled just before they're
executed. This is accomplished by using Pyalect_ to hook a transpiler into Pythons
import system. The :class:`~idom.dialect.HtmlDialectTranspiler` which implements
Pyalect_'s :class:`~pyalect.dialect.Transpiler` interface using some tooling from
htm.py_.


.. Links
.. =====

.. _Pyalect: https://pyalect.readthedocs.io/en/latest/
.. _htm.py: https://github.com/jviide/htm.py
