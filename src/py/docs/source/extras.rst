Extra Features
==============

Optionally installable features of IDOM.

.. contents::
  :local:
  :depth: 1

To install **all** features simply run

.. code-block::

    pip install idom[all]


Compatibility with Nteract's VDOM
---------------------------------

As described in the :ref:`Specifications` section, IDOM implements a specification for
:term:`VDOM` defined by `Nteract <https://nteract.io>`_'s
`vdom <https://github.com/nteract/vdom>`_ package. As a result IDOM is compatible with
all its features (though VDOM does not support all features of IDOM yet). If you've
already installed ``vdom`` then you're all set! If you'd like to try it out just run:

.. code-block:: bash

    pip install idom[vdom]


Python Language Extension
-------------------------

IDOM includes a transpiler for writing JSX-like syntax in a normal Python file!

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
    assert html("<div/>") == {"tagName": "div"}

And that's it!


How It Works
............

Once ``idom`` has been imported at your application's entrypoint, any following modules
imported with a ``# dialect=html`` header comment get transpiled just before they're
executed. This is accomplished by using Pyalect_ to hook a transpiler into Pythons
import system. The :class:`~idom.dialect.HtmlDialectTranspiler` which implements
Pyalect_'s :class:`~pyalect.dialect.Transpiler` interface using some tooling from
htm.js_.


.. Links
.. =====

.. _Pyalect: https://pyalect.readthedocs.io/en/latest/
.. _htm.py: https://github.com/jviide/htm.py
.. _htm.js: https://github.com/developit/htm
