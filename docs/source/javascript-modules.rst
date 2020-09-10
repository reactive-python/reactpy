Javascript Modules
==================

.. note::

    This is a recent feature of IDOM. If you have a problem following this tutorial
    `post an issue <https://github.com/rmorshea/idom/issues>`__.

While IDOM is a great tool for displaying HTML and responding to browser events with
pure Python, there are other projects which already allow you to do this inside
`Jupyter Notebooks <https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Basics.html>`__
or in
`webpages <https://blog.jupyter.org/and-voil%C3%A0-f6a2c08a4a93?gi=54b835a2fcce>`__.
The real power of IDOM comes from its ability to seemlessly leverage the existing
ecosystem of
`React components <https://reactjs.org/docs/components-and-props.html>`__.

So long as your library of interest is an
`ES Module <https://hacks.mozilla.org/2018/03/es-modules-a-cartoon-deep-dive/>`__
you could install using
`Snowpack <https://www.snowpack.dev/>`__
you can use it with IDOM
You can even define your own Javascript modules which use these third party Javascript
packages.


Installing React Components
---------------------------

Before you start:

- Be sure that you've installed `npm <https://www.npmjs.com/get-npm>`__.

- We're assuming the presence of a :ref:`Display Function` for our examples.

Once you've done this you can get started right away. In this example we'll be using a
charting library for React called `Victory <https://formidable.com/open-source/victory/>`__
which can be installed using the ``idom`` CLI:

.. code-block:: bash

    idom install victory

Any standard javascript dependency specifier is allowed here. Also, if you need to
access modules within a subfolder of your desired package you must explicitely state
those submodules using the ``--exports`` option:

.. code-block:: bash

    idom install my-package@1.2.3 --exports my-package/with-a-submodule

Once the package has been succesfully installed, you can import and display the component:

.. literalinclude:: examples/victory_chart.py

.. interactive-widget:: victory_chart

.. note::

    Even though it's generally discouraged, you can install packages at runtime using the
    ``install`` parameter of a :class:`~idom.widgets.utils.Module`.


Passing Props To Components
---------------------------

So now that we can install and display a dependency we probably want to pass data or
callbacks to it. This can be done in just the same way as you learned to do when
:ref:`getting started`. In the following example we'll be using a
`Button <https://react.semantic-ui.com/elements/button/>`__
component from the
`Semantic UI <https://react.semantic-ui.com/>`__
framework. We'll register callbacks and pass props to the ``<Button/>`` just as you
would for any other element in IDOM:

.. literalinclude:: examples/primary_secondary_buttons.py

.. interactive-widget:: primary_secondary_buttons


Defining Your Own Modules
-------------------------

While it's probably best to create
`a real package <https://docs.npmjs.com/packages-and-modules/contributing-packages-to-the-registry>`__
for your Javascript, if you're just experimenting it might be easiest to quickly
hook in a module of your own making on the fly. As before, we'll be using a
:class:`~idom.widgets.utils.Module`, however this time we'll pass it a ``source``
parameter which is a file-like object. In the following example we'll use Victory again,
but this time we'll add a callback to it. Unfortunately we can't just pass it in
:ref:`like we did before <Passing Props To Components>` because Victory's event API
is a bit more complex so we've implemented a quick wrapper for it in a file ``chart.js``.

.. literalinclude:: examples/custom_chart.js
    :language: javascript

Which we can read in as a ``source`` to :class:`~idom.widgets.utils.Module`:

.. literalinclude:: examples/custom_chart.py

Click the bars to trigger an event 👇

.. interactive-widget:: custom_chart
