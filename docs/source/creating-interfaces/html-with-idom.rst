HTML With IDOM
==============

In a typical Python-base web application the resonsibility of defining the view along
with its backing data and logic are distributed between a client and server
respectively. With IDOM, both these tasks are centralized in a single place. This is
done by allowing HTML interfaces to be constructed in Python. Take a look at the two
code examples below. The one on the left shows how to make a basic title and todo list
using standard HTML while the one of the right uses IDOM in Python:

.. grid:: 2
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

            from idom import html

            html.h1("My Todo List")
            html.ul(
                html.li("Build a cool new app"),
                html.li("Share it with the world!"),
            )

What this shows is that you can recreate the same HTML layouts with IDOM using functions
from the :mod:`idom.html` module. These function share the same names as their
corresponding HTML tags. For example, the ``<h1/>`` element above has a similarly named
:func:`~idom.html.h1` function. With that said, while the code above looks similar, it's
not very useful because we haven't captured the results from these function calls in a
variable. To do this we need to wraps up layout above into a single
:func:`~idom.html.div` and assign it to a variable:

.. testcode::

    layout = html.div(
        html.h1("My Todo List"),
        html.ul(
            html.li("Build a cool new app"),
            html.li("Share it with the world!"),
        ),
    )

Having done this we can inspect what is contained in our new ``layout`` variable. As it
turns out, it holds a dictionary. Printing it produces the following output:

.. testcode::

    print(layout)

.. testoutput::
    :options: +NORMALIZE_WHITESPACE

    {
        'tagName': 'div',
        'children': [
            {
                'tagName': 'h1',
                'children': ['My Todo List']
            },
            {
                'tagName': 'ul',
                'children': [
                    {'tagName': 'li', 'children': ['Build a cool new app']},
                    {'tagName': 'li', 'children': ['Share it with the world!']}
                ]
            }
        ]
    }

This may look complicated, but let's take a moment to consider what's going on here. We
have a series of nested dictionaries that, in some way, represents the HTML structure
given above. If we look at their contents we should see a common form. Each has a
``tagName`` key which contains, as the name would suggest, the tag name of an HTML
element. Then within the ``children`` key is a list that either contains strings or
other dictionaries that represent HTML elements.

What we're seeing here is called a "virtual document object model" or :ref:`VDOM`. This
is just a fancy way of saying we have a representation of the document object model or
`DOM
<https://en.wikipedia.org/wiki/Document_Object_Model#:~:text=The%20Document%20Object%20Model%20(DOM,document%20with%20a%20logical%20tree.&text=Nodes%20can%20have%20event%20handlers%20attached%20to%20them.>`__
that is not the actual DOM. We'll talk more about this concept :ref:`in the future
<Communication Scheme>`, but for now, just understand that in IDOM, we represent the
HTML document object model using dictionaries that we call VDOM.
