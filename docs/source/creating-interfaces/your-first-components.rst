Your First Component
====================

As we learned :ref:`earlier <HTML with IDOM>` we can use IDOM to make rich structured
documents out of standard HTML elements. As these documents become larger and more
complex though, working with these tiny UI elements can become difficult. When this
happens, IDOM allows you to group these elements together info "components". These
components can then be reused throughout your application.


Defining a Component
--------------------

At their core, components are just a normal Python functions that return HTML. There's
only two special things which we'll concer ourselves with there:

- We need to add a ``@component`` `decorator
  <https://realpython.com/primer-on-python-decorators/>`__
  to component function.

- By convention, we name component functions like classes - with ``CamelCase``.

So for example, if we wanted write and then :ref:`display <Running IDOM>` a ``Photo``
component we might write:

.. example:: creating_interfaces.simple_photo
    :activate-result:

.. warning::

    If we had not decorated our ``Photo`` function with the ``@component`` decorator,
    the server would start, but as soon as we tried to view the page it would be blank.
    The servers logs would then indicate:

    .. code-block:: text

        TypeError: Expected a ComponentType, not dict.


Using a Component
-----------------

Having defined our ``Photo`` component we can now nest it inside of other components:

.. example:: creating_interfaces.nested_photos
    :activate-result:
