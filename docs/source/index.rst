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

.. toctree::
    :hidden:
    :caption: Other Resources

    understanding-idom/index
    developing-idom/index
    reference-material/index
    licenses

.. toctree::
    :hidden:
    :caption: External Links

    Source Code <https://github.com/idom-team/idom>
    Community <https://github.com/idom-team/idom/discussions>
    Issues <https://github.com/idom-team/idom/issues>


IDOM is a Python web framework for building **interactive websites without needing a
single line of Javascript**. This is accomplished by breaking down complex applications
into nestable and reusable chunks of code called :ref:`"components" <Your First
Component>` that allow you to focus on what your application does rather than how it
does it.

IDOM is also ecosystem independent. It can be added to existing applications built on a
variety of sync and async web servers, as well as integrated with other frameworks like
Django, Jupyter, and Plotly Dash. Not only does this mean you're free to choose what
technology stack to run on, but on top of that, you can run the exact same components
wherever you need them. For example, you can take a component originally developed in a
Jupyter Notebook and embed it in your production application without changing anything
about the component itself.


At a Glance
-----------

To get a rough idea of how to write apps in IDOM, take a look at the tiny `"hello world"
<https://en.wikipedia.org/wiki/%22Hello,_World!%22_program>`__ application below:

.. example:: hello_world
    :activate-result:

.. note::

    Try clicking the **▶️ Result** tab to see what this displays!

So what exactly does this code do? First, it imports a few tools from ``idom`` that will
get used to describe and execute an application. Then, we create an ``App`` function
which will define the content the application displays. Specifically, it displays a kind
of HTML element called an ``h1`` `section heading
<https://developer.mozilla.org/en-US/docs/Web/HTML/Element/Heading_Elements>`__.
Importantly though, a ``@component`` decorator has been applied to the ``App`` function
to turn it into a :ref:`component <Your First Component>`. Finally, we :ref:`run
<Running IDOM>` an application server by passing the ``App`` component to the ``run()``
function.


Learning IDOM
-------------

This documentation is broken up into chapters that introduce you to concepts step by
step with detailed explanations and lots of examples. You should feel free to dive into
any section that seems interesting. While each chapter assumes knowledge from those
that came before, when you encounter a concept you're unfamiliar with you should look
for links that will help direct you to the place where it was originally taught.


Chapter 0 - :ref:`Getting Started`
-----------------------------------

If you want to follow along with examples in the sections that follow, you'll want to
start here so you can :ref:`install IDOM <Installing IDOM>`. This section also contains
more detailed information about how to :ref:`run IDOM <Running IDOM>` in different
contexts. For example, if you want to embed IDOM into an existing application, or run
IDOM within a Jupyter Notebook, this is where you can learn how to do those things.

.. grid:: 2

    .. grid-item-card::
        :link: getting-started/index.html#quick-install

        .. image:: _static/install-and-run-idom.gif

    .. grid-item-card::
        :link: getting-started/index.html

        .. image:: _static/idom-in-jupyterlab.gif


Chapter 1 - :ref:`Creating Interfaces`
--------------------------------------

...


Chapter 2 - :ref:`Adding Interactivity`
---------------------------------------

...


Chapter 3 - :ref:`Managing State`
---------------------------------

...


Chapter 4 - :ref:`Escape Hatches`
---------------------------------

...
