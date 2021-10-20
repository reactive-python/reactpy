Why IDOM?
=========

Over the `past 5 years <NPM-trends>`__ front-end developers seem to have concluded that
programs written with a declarative_ style or framework tend to be easier to understand
and maintain than those done imperatively. Put more simply, mutable state in programs
can quickly lead to unsustainable complexity. This trend is largely evidenced by the
`rise <Frontend-Frameworks-Popularity>`_ of Javascript frameworks like Vue_ and React_
which describe the logic of computations without explicitly stating their control flow.

.. _React: https://reactjs.org
.. _NPM-trends: https://www.npmtrends.com/react-vs-angular-vs-vue
.. _Vue: https://vuejs.org
.. _Declarative: https://www.youtube.com/watch?v=yGh0bjzj4IQ
.. _Frontend-Frameworks-Popularity: https://gist.github.com/tkrotoff/b1caa4c3a185629299ec234d2314e190

.. image:: /_static/npm-download-trends.png

So what does this have to do with Python and IDOM? Well, because browsers are the de
facto "operating system of the internet", even back-end languages like Python have had
to figure out clever ways to integrate with them. While standard REST_ APIs are well
suited to applications built using HTML templates, modern browser users expect a higher
degree of interactivity than this alone can achieve.

.. _REST: https://en.wikipedia.org/wiki/Representational_state_transfer

A variety of Python packages have since been created to help solve this problem:

- IPyWidgets_ - Adds interactive widgets to `Jupyter Notebooks`_
- Dash_ - Allows data scientists to produces enterprise-ready analytic apps
- Streamlit_ - Turns simple Python scripts into interactive dashboards
- Bokeh_ - An interactive visualization library for modern web browsers

.. _IPyWidgets: https://github.com/jupyter-widgets/ipywidgets
.. _Jupyter Notebooks: https://jupyter.org/
.. _Dash: https://plotly.com/dash/
.. _Streamlit: https://www.streamlit.io/
.. _Bokeh: https://docs.bokeh.org/

However they each have drawbacks that can make them difficult to use.

3. **Restrictive ecosystems** - UI components developed for one framework cannot be
   easily ported to any of the others because their APIs are either too complex,
   undocumented, or are structurally inaccesible.

1. **Imperative paradigm** - IPyWidgets and Bokeh have not embraced the same declarative
   design principles pioneered by front-end developers. Streamlit and Dash on the
   otherhand, are declarative, but fall short of the features provided by React or Vue.

1. **Limited layouts** - At their initial inception, the developers of these libraries
   were driven by the visualization needs of data scientists so the ability to create
   complex UI layouts may not have been a primary engineering goal.

As a result, IDOM was developed to help solve these problems.


Ecosystem Independence
----------------------

IDOM has a flexible set of :ref:`Core Abstractions` that allow it to interface with its
peers. At the time of writing Jupyter, Dash, and Bokeh (via Panel) are supported, while
Streamlit is in the works:

- idom-jupyter_ (try it now with Binder_)
- idom-dash_
- `IDOM in Panel`_

.. _Panel: https://panel.holoviz.org/Comparisons.html#comparing-panel-and-bokeh
.. _idom-jupyter: https://github.com/idom-team/idom-jupyter
.. _Binder: https://mybinder.org/v2/gh/idom-team/idom-jupyter/main?filepath=notebooks%2Fintroduction.ipynb
.. _idom-dash: https://github.com/idom-team/idom-dash
.. _IDOM in Panel: https://panel.holoviz.org/reference/panes/IDOM.html#panes-gallery-idom

By providing well defined interfaces and straighforward protocols, IDOM makes it easy to
swap out any part of the stack with an alternate implementation if you want to. For
example, if you need a different web server for your application, IDOM already has
several options to choose from or, use as blueprints to create your own:

- :ref:`Sanic <Sanic Servers>`
- :ref:`FastAPI <FastAPI Servers>`
- :ref:`Tornado <Tornado Servers>`
- :ref:`Flask <Flask Servers>`

You can even target your usage of IDOM in your production-grade applications with IDOM's
Javascript `React client library <idom-client-react>`_. Just install it in your
front-end app and connect to a back-end websocket that's serving up IDOM models. This
documentation acts as a prime example for this targeted usage - most of the page is
static HTML, but embedded in it are :ref:`interactive examples <Gallery>` that feature
live views being served from a web socket:

.. _idom-client-react: https://github.com/idom-team/idom/tree/main/src/idom/client/packages/idom-client-react

.. image:: /_static/live-examples-in-docs.gif


Declarative Components
----------------------

IDOM, by adopting the :ref:`Hook <Life Cycle Hooks>` design pattern from React_,
inherits many of its aesthetic and functional characteristics. For those unfamiliar with
hooks, user interfaces are composed of basic HTML elements that are constructed and
returned by special functions called "components". Then, through the magic of hooks,
those component functions can be made to have state. Consider the component below which
displays a basic representation of an AND-gate:

.. example:: simple_and_gate

Note that the code never explicitely describes how to evolve the frontend view when
events occur. Instead, it declares that, given a particular state, this is how the view
should look. It's then IDOM's responsibility to figure out how to bring that declaration
into being. This behavior of defining outcomes without stating the means by which to
achieve them is what makes components in IDOM and React "declarative". For comparison, a
hypothetical, and a more imperative approach to defining the same interface might look
similar to the following:

.. code-block::

    layout = Layout()


    def make_and_gate():
        state = {"input_1": False, "input_2": False}
        output_text = html.pre()
        update_output_text(output_text, state)

        def toggle_input(index):
            state[f"input_{index}"] = not state[f"input_{index}"]
            update_output_text(output_text, state)

        return html.div(
            html.input({"type": "checkbox", "onClick": lambda event: toggle_input(1)}),
            html.input({"type": "checkbox", "onClick": lambda event: toggle_input(2)}),
            output_text,
        )


    def update_output_text(text, state):
        text.update(
            children="{input_1} AND {input_2} = {output}".format(
                input_1=state["input_1"],
                input_2=state["input_2"],
                output=state["input_1"] and state["input_2"],
            )
        )


    layout.add_element(make_and_gate())
    layout.run()

In this imperative incarnation there are several disadvantages:

1. **Refactoring is difficult** - Functions are much more specialized to their
   particular usages in ``make_and_gate`` and thus cannot be easily generalized. By
   comparison, ``use_toggle`` from the declarative implementation could be applicable to
   any scenario where boolean indicators are toggled on and off.

2. **No clear static relations** - There is no one section of code through which to
   discern the basic structure and behaviors of the view. This issue is exemplified by
   the fact that we must call ``update_output_text`` from two different locations. Once
   in the body of ``make_and_gate`` and again in the body of the callback
   ``toggle_input``. This means that, to understand what the ``output_text`` might
   contain, we must also understand all the business logic that surrounds it.

3. **Referential links cause complexity** - To evolve the view, various callbacks must
   hold references to all the elements that they will update. At the outset this makes
   writing programs difficult since elements must be passed up and down the call stack
   wherever they are needed. Considered further though, it also means that a function
   layers down in the call stack can accidentally or intentionally impact the behavior
   of ostensibly unrelated parts of the program.


Communication Scheme
--------------------

To communicate between its back-end Python server and Javascript client, IDOM uses
something called a Virtual Document Object Model (:ref:`VDOM`) to
construct a representation of the view. The VDOM is constructed on the Python side by
components. Then, as it evolves, IDOM's layout computes VDOM-diffs and wires them to its
Javascript client where it is ultimately displayed:

.. image:: /_static/idom-flow-diagram.svg

By contrast, IDOM's peers take an approach that aligns fairly closely with the
Model-View-Controller_ design pattern - the controller lives server-side (though not
always), the model is what's synchronized between the server and client, and the view is
run client-side in Javascript. To draw it out might look something like this:

.. image:: /_static/mvc-flow-diagram.svg

.. _Model-View-Controller: https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller


Javascript Integration
----------------------

If you're thinking critically about IDOM's use of a virtual DOM, you may have thought...

    Isn't wiring a virtual representation of the view to the client, even if its diffed,
    expensive?

And yes, while the performance of IDOM is sufficient for most use cases, there are
inevitably scenarios where this could be an issue. Thankfully though, just like its
peers, IDOM makes it possible to seemlesly integrate :ref:`Javascript Components`. They
can be :ref:`custom built <Custom Javascript Components>` for your use case, or you can
just leverage the existing Javascript ecosystem
:ref:`without any extra work <Dynamically Loaded Components>`:

.. example:: material_ui_switch
