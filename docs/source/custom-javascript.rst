Custom Javascript
=================

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

So long as your library of interest can be installed NPM_, you can use it with IDOM
You can even define your own Javascript modules which use these third party Javascript
packages.


Installing React Components
---------------------------

.. note::

    Be sure that you `install NPM`_ before continuing.

In this example we'll be using the ubiquitous React-based UI framework `Material UI`_
which can be easily installed using the ``idom`` CLI:

.. code-block:: bash

    idom install @material-ui/core

Any standard javascript dependency specifier is allowed here. Also, if you need to
access modules within a subfolder of your desired package you must explicitely state
those submodules using the ``--exports`` option:

.. code-block:: bash

    idom install my-package@1.2.3 --exports my-package/with-a-submodule

Once the package has been succesfully installed, you can import and display the element:

.. example:: material_ui_button_no_action


Passing Props To Components
---------------------------

So now that we can install and display a Material UI Button we probably want to make it
do something. Thankfully there's nothing new to learn here, you can pass event handlers
to the button just as you did when :ref:`getting started`. Thus, all we need to do is
add an ``onClick`` handler to the element:

.. example:: material_ui_button_on_click


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
is a bit more complex so we've implemented a quick wrapper for it in a file ``chart.js``
which we can read in as a ``source`` to :class:`~idom.widgets.utils.Module`:

Click the bars to trigger an event 👇

.. example:: custom_chart


Alternate Client Implementations
--------------------------------

under construction...


.. Links
.. =====

.. _Material UI: https://material-ui.com/
.. _NPM: https://www.npmjs.com
.. _install NPM: https://www.npmjs.com/get-npm
