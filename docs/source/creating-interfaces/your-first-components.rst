Your First Components
=====================

As we learned :ref:`earlier <HTML with IDOM>` we can use IDOM to make rich structured
documents out of standard HTML elements. As these documents become larger and more
complex though, working with these tiny UI elements can become difficult. When this
happens, IDOM allows you to group these elements together info "components". These
components can then be reused throughout your application.


Defining a Component
--------------------

At their core, components are just normal Python functions that return HTML. To define a
component you just need to add a ``@component`` `decorator
<https://realpython.com/primer-on-python-decorators/>`__ to a function. Functions
decorator in this way are known as **render function** and, by convention, we name them
like classes - with ``CamelCase``. So consider what we would do if we wanted to write,
and then :ref:`display <Running IDOM>` a ``Photo`` component:

.. idom:: _examples/simple_photo
    :activate-result:

.. warning::

    If we had not decorated our ``Photo``'s render function with the ``@component``
    decorator, the server would start, but as soon as we tried to view the page it would
    be blank. The servers logs would then indicate:

    .. code-block:: text

        TypeError: Expected a ComponentType, not dict.


Using a Component
-----------------

Having defined our ``Photo`` component we can now nest it inside of other components. We
can define a "parent" ``Gallery`` component that returns one or more ``Profile``
components. This is part of what makes components so powerful - you can define a
component once and use it wherever and however you need to:

.. idom:: _examples/nested_photos
    :activate-result:


Parametrizing Components
------------------------

Since components are just regular functions, you can add parameters to them. This allows
parent components to pass information to child components. Where standard HTML elements
are parametrized by dictionaries, since components behave like typical functions you can
give them positional and keyword arguments as you would normally:

.. idom:: _examples/parametrized_photos
    :activate-result:


Conditional Rendering
---------------------

Your components will often need to display different things depending on different
conditions. Let's imagine that we had a basic todo list where only some of the items
have been completed. Below we have a basic implementation for such a list except that
the ``Item`` component doesn't change based on whether it's ``done``:

.. idom:: _examples/todo_list
    :activate-result:

Let's imagine that we want to add a ✔ to the items which have been marked ``done=True``.
One way to do this might be to write an ``if`` statement where we return one ``li``
element if the item is ``done`` and a different one if it's not:

.. idom:: _examples/bad_conditional_todo_list
    :activate-result:

As you can see this accomplishes our goal! However, notice how similar ``html.li(name, "
✔")`` and ``html.li(name)`` are. While in this case it isn't especially harmful, we
could make our code a little easier to read and maintain by using an "inline" ``if``
statement.

.. idom:: _examples/good_conditional_todo_list
    :activate-result:
