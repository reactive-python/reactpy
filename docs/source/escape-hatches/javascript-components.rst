.. _Javascript Component:

Javascript Components
=====================

While IDOM is a great tool for displaying HTML and responding to browser events with
pure Python, there are other projects which already allow you to do this inside
`Jupyter Notebooks <https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Basics.html>`__
or in standard
`web apps <https://blog.jupyter.org/and-voil%C3%A0-f6a2c08a4a93?gi=54b835a2fcce>`__.
The real power of IDOM comes from its ability to seamlessly leverage the existing
Javascript ecosystem. This can be accomplished in different ways for different reasons:

.. list-table::
    :header-rows: 1

    *   - Integration Method
        - Use Case

    *   - :ref:`Dynamically Loaded Components`
        - You want to **quickly experiment** with IDOM and the Javascript ecosystem.

    *   - :ref:`Custom Javascript Components`
        - You want to create polished software that can be **easily shared** with others.


.. _Dynamically Loaded Component:

Dynamically Loaded Components
-----------------------------

.. note::

    This method is not recommended in production systems - see :ref:`Distributing
    Javascript` for more info. Instead, it's best used during exploratory phases of
    development.

IDOM makes it easy to draft your code when you're in the early stages of development by
using a CDN_ to dynamically load Javascript packages on the fly. In this example we'll
be using the ubiquitous React-based UI framework `Material UI`_.

.. example:: material_ui_button_no_action

So now that we can display a Material UI Button we probably want to make it do
something. Thankfully there's nothing new to learn here, you can pass event handlers to
the button just as you did when :ref:`getting started <handling events>`. Thus, all we
need to do is add an ``onClick`` handler to the component:

.. example:: material_ui_button_on_click


.. _Custom Javascript Component:

Custom Javascript Components
----------------------------

For projects that will be shared with others, we recommend bundling your Javascript with
Rollup_ or Webpack_ into a `web module`_. IDOM also provides a `template repository`_
that can be used as a blueprint to build a library of React components.

To work as intended, the Javascript bundle must export a function ``bind()`` that
adheres to the following interface:

.. code-block:: typescript

    type EventData = {
        target: string;
        data: Array<any>;
    }

    type LayoutContext = {
        sendEvent(data: EventData) => void;
        loadImportSource(source: string, sourceType: "NAME" | "URL") => Module;
    }

    type bind = (node: HTMLElement, context: LayoutContext) => ({
        create(type: any, props: Object, children: Array<any>): any;
        render(element): void;
        unmount(): void;
    });

.. note::

    - ``node`` is the ``HTMLElement`` that ``render()`` should mount to.

    - ``context`` can send events back to the server and load "import sources"
      (like a custom component module).

    - ``type``is a named export of the current module, or a string (e.g. ``"div"``,
      ``"button"``, etc.)

    - ``props`` is an object containing attributes and callbacks for the given
      ``component``.

    - ``children`` is an array of elements which were constructed by recursively calling
      ``create``.

The interface returned by ``bind()`` can be thought of as being similar to that of
React.

- ``create`` ➜ |React.createElement|_
- ``render`` ➜ |ReactDOM.render|_
- ``unmount`` ➜ |ReactDOM.unmountComponentAtNode|_

.. |React.createElement| replace:: ``React.createElement``
.. _React.createElement: https://reactjs.org/docs/react-api.html#createelement

.. |ReactDOM.render| replace:: ``ReactDOM.render``
.. _ReactDOM.render: https://reactjs.org/docs/react-dom.html#render

.. |ReactDOM.unmountComponentAtNode| replace:: ``ReactDOM.unmountComponentAtNode``
.. _ReactDOM.unmountComponentAtNode: https://reactjs.org/docs/react-api.html#createelement

It will be used in the following manner:

.. code-block:: javascript

    // once on mount
    const binding = bind(node, context);

    // on every render
    let element = binding.create(type, props, children)
    binding.render(element);

    // once on unmount
    binding.unmount();

The simplest way to try this out yourself though, is to hook in a simple hand-crafted
Javascript module that has the requisite interface. In the example to follow we'll
create a very basic SVG line chart. The catch though is that we are limited to using
Javascript that can run directly in the browser. This means we can't use fancy syntax
like `JSX <https://reactjs.org/docs/introducing-jsx.html>`__ and instead will use
`htm <https://github.com/developit/htm>`__ to simulate JSX in plain Javascript.

.. example:: super_simple_chart


.. Links
.. =====

.. _Material UI: https://material-ui.com/
.. _CDN: https://en.wikipedia.org/wiki/Content_delivery_network
.. _template repository: https://github.com/idom-team/idom-react-component-cookiecutter
.. _web module: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules
.. _Rollup: https://rollupjs.org/guide/en/
.. _Webpack: https://webpack.js.org/
