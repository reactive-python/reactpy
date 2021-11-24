.. _Representing HTML:

Representing HTML 🚧
====================

.. note::

    Under construction 🚧

We've already discussed how to contruct HTML with IDOM in a :ref:`previous section <HTML
with IDOM>`, but we skimmed over the question of the data structure we use to represent
it. Let's reconsider the examples from before - on the top is some HTML and on the
bottom is the corresponding code to create it in IDOM:

.. code-block:: html

    <div>
        <h1>My Todo List</h1>
        <ul>
            <li>Build a cool new app</li>
            <li>Share it with the world!</li>
        </ul>
    </div>

.. testcode::

    from idom import html

    layout = html.div(
        html.h1("My Todo List"),
        html.ul(
            html.li("Build a cool new app"),
            html.li("Share it with the world!"),
        )
    )

Since we've captured our HTML into out the ``layout`` variable, we can inspect what it
contains. And, as it turns out, it holds a dictionary. Printing it produces the
following output:

.. testsetup::

    from pprint import pprint
    print = lambda *args, **kwargs: pprint(*args, **kwargs, sort_dicts=False)

.. testcode::

    assert layout == {
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
that is not the actual DOM.
