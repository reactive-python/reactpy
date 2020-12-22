Javascript Modules
==================

While IDOM is a great tool for displaying HTML and responding to browser events with
pure Python, there are other projects which already allow you to do this inside
`Jupyter Notebooks <https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Basics.html>`__
or in
`webpages <https://blog.jupyter.org/and-voil%C3%A0-f6a2c08a4a93?gi=54b835a2fcce>`__.
The real power of IDOM comes from its ability to seemlessly leverage the existing
ecosystem of
`React components <https://reactjs.org/docs/components-and-props.html>`__.
This can be accomplished in different ways for different reasons:

.. list-table::
    :header-rows: 1

    *   - Integration Method
        - Use Case

    *   - :ref:`Dynamically Install Javascript` (requires NPM_)
        - You want to **quickly experiment** with IDOM and the Javascript ecosystem.

    *   - :ref:`Import Javascript Source`
        - You want to create polished software that can be **easily shared** with others.


Dynamically Install Javascript
------------------------------

.. warning::

    Before continuing `install NPM`_.

IDOM makes it easy to draft your code when you're in the early stages of development by
using NPM_ to directly install Javascript packages into IDOM on the fly. Ultimately
though, this approach isn't recommended if you
:ref:`Import Javascript Source`.

Experimenting with IDOM it can be useful to quickly In this example we'll be using the ubiquitous React-based UI framework `Material UI`_
which can be easily installed using the ``idom`` CLI:

.. code-block:: bash

    idom install @material-ui/core

Or at runtime with :func:`idom.client.module.install` (this is useful if you're working
in a REPL or a Jupyter Notebook):

.. code-block::

    import idom
    material_ui = idom.install("@material-ui/core")
    # or install multiple modules at once
    material_ui, *other_modules = idom.install(["@material-ui/core", ...])

.. note::

    Any standard javascript dependency specifier is allowed here.

Once the package has been succesfully installed, you can import and display the element:

.. example:: material_ui_button_no_action


Passing Props To Javascript
---------------------------

So now that we can install and display a Material UI Button we probably want to make it
do something. Thankfully there's nothing new to learn here, you can pass event handlers
to the button just as you did when :ref:`getting started`. Thus, all we need to do is
add an ``onClick`` handler to the element:

.. example:: material_ui_button_on_click


Import Javascript Source
------------------------

.. note::

    This does not require NPM_ to be installed.

While it's probably best to create
`a real package <https://docs.npmjs.com/packages-and-modules/contributing-packages-to-the-registry>`__
for your Javascript, if you're just experimenting it might be easiest to quickly
hook in a module of your own making on the fly. As before, we'll be using a
:class:`~idom.client.module.Module`, however this time we'll pass it a ``source``
parameter which is a file-like object. In the following example we'll use Victory again,
but this time we'll add a callback to it. Unfortunately we can't just pass it in
:ref:`like we did before <Passing Props To Javascript>` because Victory's
event API is a bit more complex so we've implemented a quick wrapper for it in a file
``chart.js`` which we can read in as a ``source`` to :class:`~idom.client.module.Module`:

Click the bars to trigger an event 👇

.. example:: super_simple_chart


Alternate Client Implementations
--------------------------------

under construction...


.. Links
.. =====

.. _Material UI: https://material-ui.com/
.. _NPM: https://www.npmjs.com
.. _install NPM: https://www.npmjs.com/get-npm
