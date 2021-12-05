IDOM
====

.. toctree::
    :hidden:
    :caption: User Guide

    getting-started/index
    creating-interfaces/index
    adding-interactivity/index
    managing-state/index
    escape-hatches/index
    understanding-idom/index

.. toctree::
    :hidden:
    :caption: Other Resources

    developing-idom/index
    reference-material/index
    credits-and-licenses

.. toctree::
    :hidden:
    :caption: External Links

    Source Code <https://github.com/idom-team/idom>
    Community <https://github.com/idom-team/idom/discussions>
    Issues <https://github.com/idom-team/idom/issues>


IDOM is a Python web framework for building **interactive websites without needing a
single line of Javascript**. This is accomplished by breaking down complex applications
into nestable and reusable chunks of code called :ref:`"components" <Your First
Components>` that allow you to focus on what your application does rather than how it
does it.

IDOM is also ecosystem independent. It can be added to existing applications built on a
variety of sync and async web servers, as well as integrated with other frameworks like
Django, Jupyter, and Plotly Dash. Not only does this mean you're free to choose what
technology stack to run on, but on top of that, you can run the exact same components
wherever you need them. Consider the case where, you can take a component originally
developed in a Jupyter Notebook and embed it in your production application without
changing anything about the component itself.


At a Glance
-----------

To get a rough idea of how to write apps in IDOM, take a look at the tiny `"hello world"
<https://en.wikipedia.org/wiki/%22Hello,_World!%22_program>`__ application below:

.. idom:: getting-started/_examples/hello_world
    :activate-result:

.. hint::

    Try clicking the **▶️ result** tab to see what this displays!

So what exactly does this code do? First, it imports a few tools from ``idom`` that will
get used to describe and execute an application. Then, we create an ``App`` function
which will define the content the application displays. Specifically, it displays a kind
of HTML element called an ``h1`` `section heading
<https://developer.mozilla.org/en-US/docs/Web/HTML/Element/Heading_Elements>`__.
Importantly though, a ``@component`` decorator has been applied to the ``App`` function
to turn it into a :ref:`component <Your First Components>`. Finally, we :ref:`run
<Running IDOM>` an application server by passing the ``App`` component to the ``run()``
function.


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

.. grid:: 2

    .. grid-item::

        .. image:: _static/install-and-run-idom.gif

    .. grid-item::

        .. image:: getting-started/_static/idom-in-jupyterlab.gif

.. card::
    :link: getting-started/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Install IDOM and run it in a variety of different ways - with different web servers
    and frameworks. You'll even embed IDOM into an existing app.


Chapter 2 - :ref:`Creating Interfaces`
--------------------------------------

IDOM is a Python package for making user interfaces (UI). These interfaces are built
from small elements of functionality like buttons text and images. IDOM allows you to
combine these elements into reusable, nestable :ref:`"components" <your first
components>`. In the sections that follow you'll learn how these UI elements are created
and organized into components. Then, you'll use this knowledge to create interfaces from
raw data:

.. idom:: creating-interfaces/_examples/todo_list_with_keys
    :activate-result:

.. card::
    :link: creating-interfaces/index
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

.. idom:: adding-interactivity/_examples/adding_state_variable
    :activate-result:

In IDOM, ``use_state``, as well as any other function whose name starts with ``use``, is
called a "hook". These are special functions that should only be called while IDOM is
:ref:`rendering <the rendering process>`. They let you "hook into" the different
capabilities of IDOM's components of which ``use_state`` is just one (well get into the
other :ref:`later <managing state>`).

.. card::
    :link: adding-interactivity/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Under construction 🚧



Chapter 4 - :ref:`Managing State`
---------------------------------

.. card::
    :link: managing-state/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Under construction 🚧



Chapter 5 - :ref:`Escape Hatches`
---------------------------------

.. card::
    :link: escape-hatches/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Under construction 🚧


Chapter 6 - :ref:`Understanding IDOM`
-------------------------------------

.. card::
    :link: escape-hatches/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Under construction 🚧

