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

    *   - :ref:`Dynamically Loaded Components`
        - You want to **quickly experiment** with IDOM and the Javascript ecosystem.

    *   - :ref:`Custom Javascript Components`
        - You want to create polished software that can be **easily shared** with others.


Dynamically Loaded Components
-----------------------------

.. note::

    This method is not recommended in production systems - see
    :ref:`Distributing Javascript Components` for more info.

IDOM makes it easy to draft your code when you're in the early stages of development by
using a CDN_ to dynamically load Javascript packages on the fly. In this example we'll
be using the ubiquitous React-based UI framework `Material UI`_.

.. example:: material_ui_button_no_action

So now that we can display a Material UI Button we probably want to make it do
something. Thankfully there's nothing new to learn here, you can pass event handlers to
the button just as you did when :ref:`getting started`. Thus, all we need to do is add
an ``onClick`` handler to the component:

.. example:: material_ui_button_on_click


Custom Javascript Components
----------------------------

For projects that will be shared with others, we recommend bundling your Javascript with
`rollup <https://rollupjs.org/guide/en/>`__ or `webpack <https://webpack.js.org/>`__
into a
`web module <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules>`__.
IDOM also provides a
`template repository <https://github.com/idom-team/idom-react-component-cookiecutter>`__
that can be used as a blueprint to build a library of React components.

To work as intended, the Javascript bundle must provide named exports for the following
functions as well as any components that will be rendered.

.. note::

    The exported components do not have to be React-based since you'll have full control
    over the rendering mechanism.

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

And will be called in the following manner, where ``component`` is a named export of
your module:

.. code-block::

    // on every render
    renderElement(createElement(component, props), container);
    // on unmount
    unmountElement(container);

The simplest way to try this out yourself though, is to hook in a simple hand-crafted
Javascript module that has the requisite interface. In the example to follow we'll
create a very basic SVG line chart. The catch though is that we are limited to using
Javascript that can run directly in the browser. This means we can't use fancy syntax
like `JSX <https://reactjs.org/docs/introducing-jsx.html>`__ and instead will use
`htm <https://github.com/developit/htm>`__ to simulate JSX in plain Javascript.

.. example:: super_simple_chart


Distributing Javascript Components
----------------------------------

There are two ways that you can distribute your :ref:`Custom Javascript Components`:

- In a Python package via PyPI_
- Using a CDN_

That can be subsequently loaded using the respective functions:

- :func:`~idom.web.module.module_from_file`
- :func:`~idom.web.module.module_from_url`

These options are not mutually exclusive though - if you upload your Javascript
components to NPM_ and also bundle your Javascript inside a Python package, in principle
your users can determine which option work best for them. Regardless though, either you
or, if you give then the choice, your users, will have to consider the tradeoffs of
either approach.

- Distribution via PyPI_ - This method is ideal for local usage since the user can
  server all the Javascript components they depend on from their computer without
  requiring a network connection.

- Distribution via a CDN_ - Most useful in production-grade applications where its assumed
  the user has a network connection. In this scenario a CDN's
  `edge network <https://en.wikipedia.org/wiki/Edge_computing>`__ can be used to bring
  the Javascript source closer to the user in order to reduce page load times.


.. Links
.. =====

.. _Material UI: https://material-ui.com/
.. _NPM: https://www.npmjs.com
.. _install NPM: https://www.npmjs.com/get-npm
.. _CDN: https://en.wikipedia.org/wiki/Content_delivery_network
.. _PyPI: https://pypi.org/
