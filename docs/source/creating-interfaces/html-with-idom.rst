HTML With IDOM
==============

In a typical Python-base web application the resonsibility of defining the view along
with its backing data and logic are distributed between a client and server
respectively. With IDOM, both these tasks are centralized in a single place. This is
done by allowing HTML interfaces to be constructed in Python. Take a look at the two
code examples below. The one on the left shows how to make a basic title and todo list
using standard HTML, the one of the right uses IDOM in Python, and below is a view of
what the HTML would look like if displayed:

.. grid:: 1 1 2 2
    :margin: 0
    :padding: 0

    .. grid-item::
        :columns: 6

        .. code-block:: html

            <h1>My Todo List</h1>
            <ul>
                <li>Build a cool new app</li>
                <li>Share it with the world!</li>
            </ul>

    .. grid-item::
        :columns: 6

        .. testcode::

            from idom import html

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

What this shows is that you can recreate the same HTML layouts with IDOM using functions
from the :mod:`idom.html` module. These function share the same names as their
corresponding HTML tags. For instance, the ``<h1/>`` element above has a similarly named
:func:`~idom.html.h1` function. With that said, while the code above looks similar, it's
not very useful because we haven't captured the results from these function calls in a
variable. To do this we need to wrap up the layout above into a single
:func:`~idom.html.div` and assign it to a variable:

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
display an image? In HTMl we'd use the `<img/>` element and add attributes to it order
to specify a URL to its ``src`` and use some ``style`` to modify and position it:

.. code-block:: html

    <img
        src="https://picsum.photos/id/237/500/300"
        style="width: 50%; margin-left: 25%;"
        alt="Billie Holiday"
    />

In IDOM we add these attributes to elements using dictionaries. There are some notable
differences though. The biggest being the fact that all names in IDOM use ``camelCase``
instead of dash-sepearted words. For example, ``margin-left`` becomes ``marginLeft``.
Additionally, instead of specifying ``style`` using a string, we use a dictionary:

.. testcode::

    html.img(
        {
            "src": "https://picsum.photos/id/237/500/300",
            "style": {"width": "50%", "marginLeft": "25%"},
            "alt": "Billie Holiday",
        }
    )

.. raw:: html

    <img
        src="https://picsum.photos/id/237/500/300"
        style="width: 50%; margin-left: 25%;"
        alt="Billie Holiday"
    />


----------


.. card::
    :link: /understanding-idom/representing-html
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Dive into the data structures IDOM uses to represent HTML
