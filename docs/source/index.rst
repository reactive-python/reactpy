.. card::

    This documentation is still under construction 🚧. We welcome your `feedback
    <https://github.com/idom-team/idom/discussions>`__!


What is IDOM?
=============

.. toctree::
    :hidden:
    :caption: Guides

    guides/getting-started/index
    guides/creating-interfaces/index
    guides/adding-interactivity/index
    guides/managing-state/index
    guides/escape-hatches/index
    guides/understanding-idom/index

.. toctree::
    :hidden:
    :caption: Reference

    reference/browser-events
    reference/hooks-api
    _auto/apis
    reference/javascript-api
    reference/specifications

.. toctree::
    :hidden:
    :caption: About

    about/changelog
    about/contributor-guide
    about/credits-and-licenses
    Source Code <https://github.com/idom-team/idom>
    Community <https://github.com/idom-team/idom/discussions>


IDOM is a Python web framework for building **interactive websites without needing a
single line of Javascript**. This is accomplished by breaking down complex applications
into nestable and reusable chunks of code called :ref:`"components" <Your First
Components>` that allow you to focus on what your application does rather than how it
does it.

Ecosystem independence is also a core feature of IDOM. It can be added to existing
applications built on a variety of sync and async web servers, as well as integrated
with other frameworks like Django, Jupyter, and Plotly Dash. Not only does this mean
you're free to choose what technology stack to run on, but on top of that, you can run
the exact same components wherever you need them. For example, you can take a component
originally developed in a Jupyter Notebook and embed it in your production application
without changing anything about the component itself.


At a Glance
-----------

To get a rough idea of how to write apps in IDOM, take a look at the tiny `"hello world"
<https://en.wikipedia.org/wiki/%22Hello,_World!%22_program>`__ application below:

.. idom:: guides/getting-started/_examples/hello_world

.. hint::

    Try clicking the **▶️ result** tab to see what this displays!

So what exactly does this code do? First, it imports a few tools from ``idom`` that will
get used to describe and execute an application. Then, we create an ``App`` function
which will define the content the application displays. Specifically, it displays a kind
of HTML element called an ``h1`` `section heading
<https://developer.mozilla.org/en-US/docs/Web/HTML/Element/Heading_Elements>`__.
Importantly though, a ``@component`` decorator has been applied to the ``App`` function
to turn it into a :ref:`component <Your First Components>`. Finally, we :ref:`run
<Running IDOM>` a development web server by passing the ``App`` component to the
``run()`` function.

.. note::

    See :ref:`Running IDOM in Production` to learn how to use a production-grade server
    to run IDOM.


Learning IDOM
-------------

This documentation is broken up into chapters and sections that introduce you to
concepts step by step with detailed explanations and lots of examples. You should feel
free to dive into any content that seems interesting. While each chapter assumes
knowledge from those that came before, when you encounter a concept you're unfamiliar
with you should look for links that will help direct you to the place where it was
originally taught.


Chapter 1 - :ref:`Getting Started`
-----------------------------------

If you want to follow along with examples in the sections that follow, you'll want to
start here so you can :ref:`install IDOM <Installing IDOM>`. This section also contains
more detailed information about how to :ref:`run IDOM <Running IDOM>` in different
contexts. For example, if you want to embed IDOM into an existing application, or run
IDOM within a Jupyter Notebook, this is where you can learn how to do those things.

.. grid:: 1 2 2 2

    .. grid-item::

        .. image:: _static/install-and-run-idom.gif

    .. grid-item::

        .. image:: guides/getting-started/_static/idom-in-jupyterlab.gif

.. card::
    :link: guides/getting-started/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Install IDOM and run it in a variety of different ways - with different web servers
    and frameworks. You'll even embed IDOM into an existing app.


Chapter 2 - :ref:`Creating Interfaces`
--------------------------------------

IDOM is a Python package for making user interfaces (UI). These interfaces are built
from small elements of functionality like buttons text and images. IDOM allows you to
combine these elements into reusable :ref:`"components" <your first components>`. In the
sections that follow you'll learn how these UI elements are created and organized into
components. Then, you'll use this knowledge to create interfaces from raw data:

.. idom:: guides/creating-interfaces/rendering-data/_examples/todo_list_with_keys

.. card::
    :link: guides/creating-interfaces/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Learn to construct user interfaces from basic HTML elements and reusable components.


Chapter 3 - :ref:`Adding Interactivity`
---------------------------------------

Components often need to change what’s on the screen as a result of an interaction. For
example, typing into the form should update the input field, clicking a “Comment” button
should bring up a text input field, clicking “Buy” should put a product in the shopping
cart. Components need to “remember” things like the current input value, the current
image, the shopping cart. In IDOM, this kind of component-specific memory is created and
updated with a "hook" called ``use_state()`` that creates a **state variable** and
**state setter** respectively:

.. idom:: guides/adding-interactivity/components-with-state/_examples/adding_state_variable

In IDOM, ``use_state``, as well as any other function whose name starts with ``use``, is
called a "hook". These are special functions that should only be called while IDOM is
:ref:`rendering <the rendering process>`. They let you "hook into" the different
capabilities of IDOM's components of which ``use_state`` is just one (well get into the
other :ref:`later <managing state>`).

.. card::
    :link: guides/adding-interactivity/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Learn how user interfaces can be made to respond to user interaction in real-time.


Chapter 4 - :ref:`Managing State`
---------------------------------

.. card::
    :link: guides/managing-state/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Under construction 🚧



Chapter 5 - :ref:`Escape Hatches`
---------------------------------

.. card::
    :link: guides/escape-hatches/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Under construction 🚧


Chapter 6 - :ref:`Understanding IDOM`
-------------------------------------

.. card::
    :link: guides/escape-hatches/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Under construction 🚧

