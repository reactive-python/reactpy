HTML With ReactPy
=================

In a typical Python-base web application the responsibility of defining the view along
with its backing data and logic are distributed between a client and server
respectively. With ReactPy, both these tasks are centralized in a single place. This is
done by allowing HTML interfaces to be constructed in Python. Take a look at the two
code examples below. The first one shows how to make a basic title and todo list using
standard HTML, the second uses ReactPy in Python, and below is a view of what the HTML
would look like if displayed:

.. grid:: 1 1 2 2
    :margin: 0
    :padding: 0

    .. grid-item::

        .. code-block:: html

            <h1>My Todo List</h1>
            <ul>
                <li>Build a cool new app</li>
                <li>Share it with the world!</li>
            </ul>

    .. grid-item::

        .. testcode::

            from reactpy import html

            html.h1("My Todo List")
            html.ul(
                html.li("Build a cool new app"),
                html.li("Share it with the world!"),
            )

    .. grid-item-card::
        :columns: 12

        .. raw:: html

            <div style="width: 50%; margin: auto;">
                <h2 style="margin-top: 0px !important;">My Todo List</h2>
                <ul>
                    <li>Build a cool new app</li>
                    <li>Share it with the world!</li>
                </ul>
            </div>

What this shows is that you can recreate the same HTML layouts with ReactPy using functions
from the :mod:`reactpy.html` module. These function share the same names as their
corresponding HTML tags. For instance, the ``<h1/>`` element above has a similarly named
:func:`~reactpy.html.h1` function. With that said, while the code above looks similar, it's
not very useful because we haven't captured the results from these function calls in a
variable. To do this we need to wrap up the layout above into a single
:func:`~reactpy.html.div` and assign it to a variable:

.. testcode::

    layout = html.div(
        html.h1("My Todo List"),
        html.ul(
            html.li("Build a cool new app"),
            html.li("Share it with the world!"),
        ),
    )


Adding HTML Attributes
----------------------

That's all well and good, but there's more to HTML than just text. What if we wanted to
display an image? In HTMl we'd use the ``<img>`` element and add attributes to it order
to specify a URL to its ``src`` and use some ``style`` to modify and position it:

.. code-block:: html

    <img
        src="https://picsum.photos/id/237/500/300"
        class="img-fluid"
        style="width: 50%; margin-left: 25%;"
        alt="Billie Holiday"
        tabindex="0"
    />

In ReactPy we add these attributes to elements using a dictionary:

.. testcode::

    html.img(
        {
            "src": "https://picsum.photos/id/237/500/300",
            "class_name": "img-fluid",
            "style": {"width": "50%", "margin_left": "25%"},
            "alt": "Billie Holiday",
        }
    )

.. raw:: html

    <!-- no tabindex since that would ruin accessibility of the page -->
    <img
        src="https://picsum.photos/id/237/500/300"
        class="img-fluid"
        style="width: 50%; margin-left: 25%;"
        alt="Billie Holiday"
    />

There are some notable differences. First, all names in ReactPy use ``snake_case`` instead
of dash-separated words. For example, ``tabindex`` and ``margin-left`` become
``tab_index`` and ``margin_left`` respectively. Second, instead of using a string to
specify the ``style`` attribute, we use a dictionary to describe the CSS properties we
want to apply to an element. This is done to avoid having to escape quotes and other
characters in the string. Finally, the ``class`` attribute is renamed to ``class_name``
to avoid conflicting with the ``class`` keyword in Python.

For full list of supported attributes and differences from HTML, see the
:ref:`HTML Attributes` reference.

----------


.. card::
    :link: /guides/understanding-reactpy/representing-html
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Dive into the data structures ReactPy uses to represent HTML
