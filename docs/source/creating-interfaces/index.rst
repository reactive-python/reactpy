Creating Interfaces
===================

.. toctree::
    :hidden:

    html-with-idom
    your-first-component
    parametrizing-components
    conditional-rendering
    dynamic-layout-structure

.. dropdown:: :octicon:`bookmark-fill;2em` What You'll Learn
    :color: info
    :animate: fade-in

    .. grid:: 2

        .. grid-item-card:: :octicon:`mortar-board` Intro to HTML
            :link: html-with-idom
            :link-type: doc

            Learn how to construct HTML layouts with IDOM.

        .. grid-item-card:: :octicon:`package` Your First Component
            :link: your-first-component
            :link-type: doc

            Discover what components are and why their one of IDOM's foundational
            concepts.

        .. grid-item-card:: :octicon:`plug` Parametrizing Components
            :link: parametrizing-components
            :link-type: doc

            Leverage the reusability of components by passing them arguments

        .. grid-item-card:: :octicon:`code-square` Conditional Rendering
            :link: conditional-rendering
            :link-type: doc

            Use what you've learned so far to add conditional logic to your components.

        .. grid-item-card:: :octicon:`versions` Dynamic Layout Structure
            :link: dynamic-layout-structure
            :link-type: doc

            Understand how IDOM keeps track of changing layout structures.

IDOM is a Python package for making user interfaces (UI). These interfaces are built
from small elements of functionality like buttons text and images. IDOM allows you to
combine these elements into reusable, nestable :ref:`"components" <your first
component>`. In the sections that follow you'll learn how these UI elements are created
and organized into components. Then, you'll use components to customize and
conditionally display more complex UIs.


Section 1: HTML with IDOM
-------------------------

In a typical Python-base web application the resonsibility of defining the view along
with its backing data and logic are distributed between a client and server
respectively. With IDOM, both these tasks are centralized in a single place. This is
done by allowing HTML interfaces to be constructed in Python. Let's consider the HTML
sample below:

.. code-block:: html

    <h1>My Todo List</h1>
    <ul>
        <li>Design a cool new app</li>
        <li>Build it</li>
        <li>Share it with the world!</li>
    </ul>

To recreate the same thing in IDOM you would write:

.. code-block::

    from idom import html

    html.div(
        html.h1("My Todo List"),
        html.ul(
            html.li("Design a cool new app"),
            html.li("Build it"),
            html.li("Share it with the world!"),
        )
    )

.. card::
    :link: html-with-idom
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^
    Learn how to construct HTML layouts with IDOM.


Section 2: Your First Component
-------------------------------


Section 3: Parametrizing Components
-----------------------------------


Section 4: Conditional Rendering
--------------------------------


Section 5: Dynamic Layout Structure
-----------------------------------
