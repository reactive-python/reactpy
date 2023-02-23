Creating Interfaces
===================

.. toctree::
    :hidden:

    html-with-reactpy/index
    your-first-components/index
    rendering-data/index

.. dropdown:: :octicon:`bookmark-fill;2em` What You'll Learn
    :color: info
    :animate: fade-in
    :open:

    .. grid:: 1 2 2 2

        .. grid-item-card:: :octicon:`code-square` HTML with ReactPy
            :link: html-with-reactpy/index
            :link-type: doc

            Construct HTML layouts from the basic units of user interface functionality.

        .. grid-item-card:: :octicon:`package` Your First Components
            :link: your-first-components/index
            :link-type: doc

            Define reusable building blocks that it easier to construct complex
            interfaces.

        .. grid-item-card:: :octicon:`database` Rendering Data
            :link: rendering-data/index
            :link-type: doc

            Use data to organize and render HTML elements and components.

ReactPy is a Python package for making user interfaces (UI). These interfaces are built
from small elements of functionality like buttons text and images. ReactPy allows you to
combine these elements into reusable, nestable :ref:`"components" <your first
components>`. In the sections that follow you'll learn how these UI elements are created
and organized into components. Then, you'll use components to customize and
conditionally display more complex UIs.


Section 1: HTML with ReactPy
----------------------------

In a typical Python-base web application the responsibility of defining the view along
with its backing data and logic are distributed between a client and server
respectively. With ReactPy, both these tasks are centralized in a single place. The most
foundational pilar of this capability is formed by allowing HTML interfaces to be
constructed in Python. Let's consider the HTML sample below:

.. code-block:: html

    <h1>My Todo List</h1>
    <ul>
        <li>Build a cool new app</li>
        <li>Share it with the world!</li>
    </ul>

To recreate the same thing in ReactPy you would write:

.. code-block::

    from reactpy import html

    html.div(
        html.h1("My Todo List"),
        html.ul(
            html.li("Design a cool new app"),
            html.li("Build it"),
            html.li("Share it with the world!"),
        )
    )

.. card::
    :link: html-with-reactpy/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Construct HTML layouts from the basic units of user interface functionality.


Section 2: Your First Components
--------------------------------

The next building block in our journey with ReactPy are components. At their core,
components are just a normal Python functions that return :ref:`HTML <HTML with ReactPy>`.
The one special thing about them that we'll concern ourselves with now, is that to
create them we need to add an ``@component`` `decorator
<https://realpython.com/primer-on-python-decorators/>`__. To see what this looks like in
practice we'll quickly make a ``Photo`` component:

.. reactpy:: your-first-components/_examples/simple_photo

.. card::
    :link: your-first-components/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Define reusable building blocks that it easier to construct complex interfaces.


Section 3: Rendering Data
-------------------------

The last pillar of knowledge you need before you can start making :ref:`interactive
interfaces <adding interactivity>` is the ability to render sections of the UI given a
collection of data. This will require you to understand how elements which are derived
from data in this way must be organized with :ref:`"keys" <Organizing Items With Keys>`.
One case where we might want to do this is if items in a todo list come from a list of
data that we want to sort and filter:

.. reactpy:: rendering-data/_examples/todo_list_with_keys

.. card::
    :link: rendering-data/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Use data to organize and render HTML elements and components.
