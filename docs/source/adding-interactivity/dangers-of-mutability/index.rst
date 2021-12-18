Dangers of Mutability
=====================

While state can hold any type of value, you should be careful to avoid directly
modifying objects that you declare as state with IDOM. In other words, you must not
:ref:`"mutate" <What is a Mutation>` values which are held as state. Rather, to change
these values you should use new ones or create copies.


.. _what is a mutation:

What is a Mutation?
-------------------

In Python, values may be either "mutable" or "immutable". Mutable objects are those
whose underlying data can be changed after they are created, and immutable objects are
those which cannot. A "mutation" then, is the act of changing the underlying data of a
mutable value. In particular, a :class:`dict` is a mutable type of value. In the code
below, an initially empty dictionary is created. Then, a key and value is added to it:

.. code-block::

    x = {}
    x["a"] = 1
    assert x == {"a": 1}

This is different from something like a :class:`str` which is immutable. Instead of
modifying the underlying data of an existing value, a new one must be created to
facilitate change:

.. code-block::

    x = "Hello"
    y = x + " world!"
    assert x is not y

.. note::

    In Python, the ``is`` and ``is not`` operators check whether two values are
    identitcal. This `is distinct
    <https://realpython.com/python-is-identity-vs-equality>`__ from checking whether two
    values are equivalent with the ``==`` or ``!=`` operators.

Thus far, all the values we've been working with have been immutable. These include
:class:`int`, :class:`float`, :class:`str`, and :class:`bool` values. As a result, we've
have not had to consider the consiquences of mutations.


Why Avoid Mutation?
-------------------

Unfortunately, IDOM does not understand that when a value is mutated, it may have
changed. As a result, mutating values will not trigger re-renders. Thus, you must be
careful to avoid mutation whenever you want IDOM to re-render a component. For example,
the intention of the code below is to make the red dot move when you touch or hover over
the preview area. However it doesn't - the dot remains stationary:

.. idom:: _examples/moving_dot_broken

The problem is with this section of code:

.. literalinclude:: _examples/moving_dot_broken.py
    :language: python
    :lines: 13-14
    :linenos:
    :lineno-start: 13

This code mutates the ``position`` dictionary from the prior render instead of using the
state variable's associated state setter. Without calling setter IDOM has no idea that
the variable's data has been modified. While it can be possible to get away with
mutating state variables, it's highly dicsouraged. Doing so can cause strange and
unpredictable behavior. As a result, you should always treat the data within a state
variable as immutable.

To actually trigger a render we need to call the state setter. To do that we'll assign
it to ``set_position`` instead of the unused ``_`` variable we have above. Then we can
call it by passing a *new* dictionary with the values for the next render. Notice how,
by making these alterations to the code, that the dot now follows your pointer when
you touch or hover over the preview:

.. idom:: _examples/moving_dot


.. dropdown:: Local mutation can be alright
    :color: info
    :animate: fade-in

    While code like this causes problems:

    .. code-block::

        position["x"] = event["clientX"] - outer_div_bounds["x"]
        position["y"] = event["clientY"] - outer_div_bounds["y"]

    It's ok if you mutate a fresh dictionary that you have *just* created before calling
    the state setter:

    .. code-block::

        new_position = {}
        new_position["x"] = event["clientX"] - outer_div_bounds["x"]
        new_position["y"] = event["clientY"] - outer_div_bounds["y"]
        set_position(new_position)

    It's actually nearly equivalent to having written:

    .. code-block::

        set_position(
            {
                "x": event["clientX"] - outer_div_bounds["x"],
                "y": event["clientY"] - outer_div_bounds["y"],
            }
        )

    Mutation is only a problem when you change data assigned to existing state
    variables. Mutating an object you’ve just created is okay because no other code
    references it yet. Changing it isn’t going to accidentally impact something that
    depends on it. This is called a “local mutation.” You can even do local mutation
    while rendering. Very convenient and completely okay!

Python provides a number of mutable built in data types:

- :ref:`Dictionaries <working with dictionaries>`
- :ref:`Lists <working with lists>`
- :ref:`Sets <working with sets>`

Below we suggest a number of strategies for safely working with these types...


Working with Dictionaries
-------------------------

There are a number of different ways to idiomatically construct dictionaries


Working with Lists
------------------


Working with Sets
-----------------


Working with Nested Data
------------------------
