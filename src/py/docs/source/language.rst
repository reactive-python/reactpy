Python Language Extension
=========================

.. warning::

    This is an experimental feature that is subject to change

IDOM also provides an optional extension to the Python language with an fstring_-like
template syntax for writing HTMl.

.. code-block::
    :emphasize-lines: 7-11

    # coding=idom
    from idom import html

    size = "30px"
    text = "Hello!"

    model = html"""
    <div height={size} width={size} >
        <p>{text}</p>
    </div>
    """

    assert model == {
        "tagName": "div",
        "attributes": {"height": "30px", "width": "30px"},
        "children": ["\n    ", {"tagName": "p", "children": ["Hello!"]}, "\n"],
    }
    ```

.. note::

    This idea was inspired by `pyxl <https://github.com/dropbox/pyxl>`__


HTML Template Usage
-------------------

Every file that uses the HTML template syntax must:

1. Have an `html` encoding indicator as its first or second line.
2. Import `idom` into its namespace.

So your files should all start a bit like this:

```python
# coding=html
import idom
```

If you haven't :ref:`permanently installed <HTML Template Syntax Installation>` the
language extension you'll need to import modules with HTML Template Syntax, you'll need
to make sure `idom` has been imported at your application's entry point to register the
language extension before importing your module:

.. code-block::

    import idom
    import my_app

    app.run()

Where ``my_app.py`` would have the following contents:

.. code-block::

    # coding=html
    from idom import html

    @idom.element
    async def Hello():
        return html"<h1>Hello!</h1>"

    app = idom.server.sanic.PerClientState(Slideshow)


HTML Template Syntax Installation
---------------------------------

If you want to more permanently install the language extension you can run the console command:

.. code-block:: bash

    idom codec register

Which can be undone (if desired) later:

.. code-block:: bash

    idom codec deregister

This is **optional**, because you can always `import idom` at the root of your application
to enable the extension. After this initial import all the follow with `coding=vdom`
will be appropriately transpiled.


Additional Support For HTML Template Syntax
-------------------------------------------

You won't be able to use the HTML template syntax directly in Python's default REPL, but
it will work out of the box with:

1. Jupyter_

2. IPython_


.. Links
.. -----
.. _Jupyter: https://jupyter.org
.. _IPython: http://ipython.org/
.. _fstring: https://www.python.org/dev/peps/pep-0498/
