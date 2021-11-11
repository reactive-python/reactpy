Your First Component
====================

The next building block in our journey with IDOM are components. At their core,
components are just a normal Python functions that return :ref:`HTML <HTML with IDOM>`.
The one special thing about them that we need to be concerned with now, is that to
create them they require the addition of the :func:`~idom.core.component.component`
decorator. Take a quick look at this "hello world" example you make have seen earlier to
check out what this looks like in practice:

.. example:: hello_world
    :activate-result:

.. note::

    Not all functions that return HTML need to be decorated with the ``@component``
    decorator - when and where they are required will be discussed when we start
    :ref:`adding interactivity`.

In the code above we have a function ``App`` that is decorated with ``@component`` to
turn it into a component. This function then gets passed to
:func:`~idom.server.prefab.run` in order to :ref:`run a server <Running IDOM>` to
display it. If we had not decorated our ``App`` function with the ``@component``
decorator, the server would start, but as soon as we tried to view the page it would be
blank. The servers logs would then indicate:

.. code-block:: text

    TypeError: Expected a ComponentType, not dict.

To see why this is we can check out what happens when we call ``App`` with and without
the ``@component`` decorator. In the first instance we get a dictionary representing our
HTML:

.. testcode::

    from idom import html

    def App():
        return html.h1("Hello, world!")

    print(App())

.. testoutput::

    {'tagName': 'h1', 'children': ['Hello, world!']}

But, if we decorate it we instead find:

.. testcode::

    from idom import component, html, ComponentType

    @component
    def App():
        return html.h1("Hello, world!")

    app = App()
    print(app)
    print(type(app))

.. testcode::
    :hide:

    import re
    # update the output code block below and this regex pattern if this fails
    assert re.match("Component\(\d+\)", str(App()))

.. code-block::

    App(7fc0d881fbd0)
    <class 'idom.core.component.Component'>

This explains the error. If we don't decorate the function we just get out out HTML
dict, but if we do, we get this special ``Component`` object back. Since the ``run``
function expects the latter to do its job we get an error about it.
