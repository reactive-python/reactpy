Creating Interfaces
===================

.. toctree::
    :hidden:

    html-with-idom
    your-first-components
    rendering-data

.. dropdown:: :octicon:`bookmark-fill;2em` What You'll Learn
    :color: info
    :animate: fade-in
    :open:

    .. grid:: 2

        .. grid-item-card:: :octicon:`mortar-board` HTML with IDOM
            :link: html-with-idom
            :link-type: doc

            Construct HTML layouts with IDOM.

        .. grid-item-card:: :octicon:`package` Your First Components
            :link: your-first-components
            :link-type: doc

            Define and use components.

        .. grid-item-card:: :octicon:`versions` Rendering Data
            :link: rendering-data
            :link-type: doc

            Render HTML elements and components from raw data

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
respectively. With IDOM, both these tasks are centralized in a single place. The most
foundational pilar of this capability is formed by allowing HTML interfaces to be
constructed in Python. Let's consider the HTML sample below:

.. code-block:: html

    <h1>My Todo List</h1>
    <ul>
        <li>Build a cool new app</li>
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

    Learn how to construct HTML layouts with IDOM and the underlying data structure we
    use to represent them.


Section 2: Your First Components
--------------------------------

The next building block in our journey with IDOM are components. At their core,
components are just a normal Python functions that return :ref:`HTML <HTML with IDOM>`.
The one special thing about them that we'll concern ourselves with now, is that to
create them we need to add an ``@component`` `decorator
<https://realpython.com/primer-on-python-decorators/>`__. To see what this looks like in
practice we'll quickly make a ``Photo`` component:

.. example:: creating_interfaces.simple_photo
    :activate-result:


Section 3: Rendering Data
-------------------------
