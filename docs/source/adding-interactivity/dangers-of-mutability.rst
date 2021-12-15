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
mutable value. For example, a :class:`dict` is a mutable type of value. In the code
below, an initially empty dictionary is created. Then, a key and value is added to it:

.. code-block::

    x = {}
    x["a"] = 1
    assert x == {"a": 1}

This is different from something like a :class:`str` which is immutable. Instead of
modifying the underlying data of an existing value, a new one must be created to
facilitate change:

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
careful to avoid mutation whenever you want IDOM to re-render a component.

.. idom:: _examples/moving_dot
