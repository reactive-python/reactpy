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

.. note::

    We're working to support non-standard packages too [GH166]_.

Installing React Components
---------------------------

Before you start:

- Be sure that you've installed `npm <https://www.npmjs.com/get-npm>`__.

- We're assuming the presence of a :ref:`Display Function` for our examples.

Once you've done this you can get started right away. In this example we'll be using a
charting library for React called `Victory <https://formidable.com/open-source/victory/>`__.
Installing it in IDOM is quite simple. Just create a :class:`~idom.widgets.utils.Module`,
tell it what to install and specify ``install=True``.

.. literalinclude:: widgets/victory_chart.py
    :lines: 1-4

.. note::

    We're working on a CLI for this [GH167]_

You can install a specific version using ``install="victory@34.1.3`` or any other
standard javascript dependency specifier. Alternatively, if you need to access a module
in a subfolder of your desired Javascript package, you can provide ``name="path/to/module"``
and ``install"my-package"``.

With that out of the way you can import a component from Victory:

.. literalinclude:: widgets/victory_chart.py
    :lines: 6

Using the ``VictoryBar`` chart component it's simple as displaying it:

.. literalinclude:: widgets/victory_chart.py
    :lines: 8

.. interactive-widget:: victory_chart


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

.. literalinclude:: widgets/primary_secondary_buttons.py

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

.. literalinclude:: widgets/custom_chart.js

Which we can read in as a ``source`` to :class:`~idom.widgets.utils.Module`:

.. literalinclude:: widgets/custom_chart.py

Click the bars to trigger an event 👇

.. interactive-widget:: custom_chart
