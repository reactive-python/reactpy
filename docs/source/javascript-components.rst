Javascript Components
=====================

While IDOM is a great tool for displaying HTML and responding to browser events with
pure Python, there are other projects which already allow you to do this inside
`Jupyter Notebooks <https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Basics.html>`__
or in
`webpages <https://blog.jupyter.org/and-voil%C3%A0-f6a2c08a4a93?gi=54b835a2fcce>`__.
The real power of IDOM comes from its ability to seamlessly leverage the existing
ecosystem of
`React components <https://reactjs.org/docs/components-and-props.html>`__.
This can be accomplished in different ways for different reasons:

.. list-table::
    :header-rows: 1

    *   - Integration Method
        - Use Case

    *   - :ref:`Custom Javascript Components`
        - You want to create polished software that can be **easily shared** with others.

    *   - :ref:`Dynamically Install Javascript` (requires NPM_)
        - You want to **quickly experiment** with IDOM and the Javascript ecosystem.


Custom Javascript Components
----------------------------

For projects that will be shared with others we recommend bundling your Javascript with
`rollup <https://rollupjs.org/guide/en/>`__ or `webpack <https://webpack.js.org/>`__
into a
`web module <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules>`__.
IDOM also provides a
`template repository <https://github.com/idom-team/idom-react-component-cookiecutter>`__
that can be used as a blueprint to build a library of React components.

The core benefit of loading Javascript in this way is that users of your code won't need
to have NPM_ installed. Rather, they can use ``pip`` to install your Python package
without any other build steps because the bundled Javascript you distributed with it
will be symlinked into the IDOM client at runtime.

To work as intended, the Javascript bundle must export the following named functions:

.. code-block:: typescript

    type createElement = (component: any, props: Object) => any;
    type renderElement = (element: any, container: HTMLElement) => void;
    type unmountElement = (element: HTMLElement) => void;

These functions can be thought of as being analogous to those from React.

- ``createElement`` ➜ |react.createElement|_
- ``renderElement`` ➜ |reactDOM.render|_
- ``unmountElement`` ➜ |reactDOM.unmountComponentAtNode|_

.. |react.createElement| replace:: ``react.createElement``
.. _react.createElement: https://reactjs.org/docs/react-api.html#createelement

.. |reactDOM.render| replace:: ``reactDOM.render``
.. _reactDOM.render: https://reactjs.org/docs/react-dom.html#render

.. |reactDOM.unmountComponentAtNode| replace:: ``reactDOM.unmountComponentAtNode``
.. _reactDOM.unmountComponentAtNode: https://reactjs.org/docs/react-api.html#createelement

And will be called in the following manner:

.. code-block::

    // on every render
    renderElement(createElement(type, props), container);
    // on unmount
    unmountElement(container);

Once you've done this, you can distribute the bundled javascript in your Python package
and integrate it into IDOM by defining :class:`~idom.client.module.Module` objects that
load them from source:

.. code-block::

    import idom
    my_js_package = idom.Module("my-js-package", source_file="/path/to/my/bundle.js")

The simplest way to try this out yourself though, is to hook in simple a hand-crafted
Javascript module that has the requisite interface. In the example to follow we'll
create a very basic SVG line chart. The catch though is that we are limited to using
Javascript that can run directly in the browser. This means we can't use fancy syntax
like `JSX <https://reactjs.org/docs/introducing-jsx.html>`__ and instead will use
`htm <https://github.com/developit/htm>`__ to simulate JSX in plain Javascript.

.. example:: super_simple_chart


.. Links
.. =====

.. _Material UI: https://material-ui.com/
.. _NPM: https://www.npmjs.com
.. _install NPM: https://www.npmjs.com/get-npm



Dynamically Install Javascript
------------------------------

.. warning::

    - Before continuing `install NPM`_.
    - Not guaranteed to work in all client implementations
      (see :attr:`~idom.config.IDOM_CLIENT_MODULES_MUST_HAVE_MOUNT`)

IDOM makes it easy to draft your code when you're in the early stages of development by
using NPM_ to directly install Javascript packages on the fly. In this example we'll be
using the ubiquitous React-based UI framework `Material UI`_ which can be installed
using the ``idom`` CLI:

.. code-block:: bash

    idom install @material-ui/core

Or at runtime with :func:`idom.client.module.install` (this is useful if you're working
in a REPL or Jupyter Notebook):

.. code-block::

    import idom
    material_ui = idom.install("@material-ui/core")
    # or install multiple modules at once
    material_ui, *other_modules = idom.install(["@material-ui/core", ...])

.. note::

    Any standard javascript dependency specifier is allowed here.

Once the package has been successfully installed, you can import and display the component:

.. example:: material_ui_button_no_action


Passing Props To Javascript Components
--------------------------------------

So now that we can install and display a Material UI Button we probably want to make it
do something. Thankfully there's nothing new to learn here, you can pass event handlers
to the button just as you did when :ref:`getting started`. Thus, all we need to do is
add an ``onClick`` handler to the component:

.. example:: material_ui_button_on_click
