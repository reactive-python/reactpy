Javascript Modules
==================

.. note::

    This is recent feature of IDOM. If you have a problem following this tutorial
    `post an issue <https://github.com/rmorshea/idom/issues>`__.

While IDOM is a great tool for displaying HTML and respond to browser events with
pure Python, there are other projects which already allow you to do this inside
`Jupyter Notebooks <https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Basics.html>`__
or in
`webpages <https://blog.jupyter.org/and-voil%C3%A0-f6a2c08a4a93?gi=54b835a2fcce>`__.
The real power of IDOM comes from its ability to seemlessly leverage the existing
ecosystem of `React components <https://reactjs.org/docs/components-and-props.html>`__.
So long as you can install a React library using `Snowpack <https://www.snowpack.dev/>`__
you can use it in your IDOM layout. You can even define your own Javascript modules
which use these third party Javascript packages.


Installing React Components
---------------------------

.. note::

    - Be sure that you've installed `npm <https://www.npmjs.com/get-npm>`__.

    - We're assuming the presence of a :ref:`Display Function` for our examples.

Once you've done this you can get started right away. In this example we'll be using a
charting library for React called `Victory <https://formidable.com/open-source/victory/>`__.
Installing it in IDOM is quite simple:

.. code-block::

    import idom
    # this may take a minute to download and install
    victory = idom.Module(name="victory", install=True)

You can install a specific version using ``install="victory@34.1.3`` or any other
standard javascript dependency specifier. Alternatively, if you need to access a module
in a subfolder of your desired Javascript package, you can provide ``name="path/to/module"``
and ``install"my-package"``.

With that out of the way can import a component from Victory:

.. code-block::

    VictoryBar = victory.Import("VictoryBar")

Using the ``VictoryBar`` chart component is as simple as displaying it:

.. code-block::

    display(VictoryBar)


Passing Props To Components
---------------------------

Under construction...


Defining Your Own Modules
-------------------------
