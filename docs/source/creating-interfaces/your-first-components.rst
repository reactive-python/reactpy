Your First Component
====================

The next building block in our journey with IDOM are components. At their core,
components are just a normal Python functions that return :ref:`HTML <HTML with IDOM>`.
The one special thing about them that we'll concern ourselves with now, is that to
create them we need to add an ``@component`` `decorator
<https://realpython.com/primer-on-python-decorators/>`__. To see what this looks like in
practice we'll put the todo list HTML from above into a component:

.. example:: creating_interfaces.static_todo_list
    :activate-result:

.. note::

    Not all functions that return HTML need to be decorated with the ``@component``
    decorator. We'll discuss when and where they are required when we start :ref:`adding
    interactivity`.

In the code above we have a function ``App`` that is decorated with ``@component`` to
turn it into a component. This function then gets passed to
:func:`~idom.server.prefab.run` in order to :ref:`run a server <Running IDOM>` to
display it. If we had not decorated our ``App`` function with the ``@component``
decorator, the server would start, but as soon as we tried to view the page it would be
blank. The servers logs would then indicate:

.. code-block:: text

    TypeError: Expected a ComponentType, not dict.

To see why this is we can check out what happens when we call ``App`` with and without
the ``@component`` decorator. In the first case we get a dictionary representing our
HTML:

.. testsetup::

    from pprint import pprint as print

.. testcode::

    from idom import html


    def App():
        return html.div(
            html.h1("My Todo List"),
            html.ul(
                html.li("Build a cool new app"),
                html.li("Share it with the world!"),
            ),
        )


    print(App())

.. testoutput::

    {'tagName': 'div',
    'children': [{'tagName': 'h1', 'children': ['My Todo List']},
                {'tagName': 'ul',
                'children': [{'tagName': 'li',
                                'children': ['Build a cool new app']},
                                {'tagName': 'li',
                                'children': ['Share it with the world!']}]}]}

But, if we decorate it we instead find:

.. testcode::

    from idom import component, html, ComponentType


    @component
    def App():
        return html.div(
            html.h1("My Todo List"),
            html.ul(
                html.li("Build a cool new app"),
                html.li("Share it with the world!"),
            ),
        )


    app = App()
    print(app)
    print(type(app))

.. testcode::
    :hide:

    import re
    # update the output code block below and this regex pattern if this fails
    assert re.match("Component\(\d+\)", str(App()))

.. code-block::  text

    App(7fc0d881fbd0)
    <class 'idom.core.component.Component'>

After making this discovery, if you did a bit of digging around in IDOM's source code,
you'd find that this ``Component`` object has a ``Component.render()`` method. And it's
when calling this method, that you'll return the HTML we might have expected initially:

.. testcode::

    print(app.render())

.. testoutput::

    {'tagName': 'div',
    'children': [{'tagName': 'h1', 'children': ['My Todo List']},
                {'tagName': 'ul',
                'children': [{'tagName': 'li',
                                'children': ['Build a cool new app']},
                                {'tagName': 'li',
                                'children': ['Share it with the world!']}]}]}

This explains the error. If we don't decorate the function we just get out out HTML
dict, but if we do, we get this special ``Component`` object back. Since the ``run()``
function expects the latter to do its job, we get an error about it.
