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


.. _Why Avoid Mutation:

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


Working with Dictionaries
-------------------------

Below are some ways to update dictionaries without mutating them:

.. card:: Updating Items
    :link: updating-dictionary-items
    :link-type: ref

    Avoid using item assignment, ``dict.update``, or ``dict.setdefault``. Instead try
    the strategies below:

    .. code-block::

        {**d, "key": value}

        # Python >= 3.9
        d | {"key": value}

        # Equivalent to setdefault()
        {"key": value, **d}

.. card:: Removing Items
    :link: removing-dictionary-items
    :link-type: ref

    Avoid using item deletion or ``dict.pop``. Instead try the strategies below:

    .. code-block::

        {
            k: v
            for k, v in d.items()
            if k != key
        }

        # Better for removing multiple items
        {
            k: d[k]
            for k in set(d).difference([key])
        }


.. _updating-dictionary-items:

Updating Dictionary Items
.........................

.. grid:: 1 1 1 2
    :gutter: 1

    .. grid-item-card:: :bdg-danger:`Avoid`

        .. code-block::

            d[key] = value

            d.update({key: value})

            d.setdefault(key, value)

    .. grid-item-card:: :bdg-info:`Prefer`

        .. code-block::

            {**d, key: value}

            # Python >= 3.9
            d | {key: value}

            # Equivalent to setdefault()
            {key: value, **d}

As we saw in an :ref:`earlier example <why avoid mutation>`, instead of mutating
dictionaries to update their items you should instead create a copy that contains the
desired changes.

However, sometimes you may only want to update some of the information in a dictionary
which is held by a state variable. Consider the case below where we have a form for
updating user information with a preview of the currently entered data. We can
accomplish this using `"unpacking" <https://www.python.org/dev/peps/pep-0448/>`__ with
the ``**`` syntax:

.. idom:: _examples/dict_update


.. _removing-dictionary-items:

Removing Dictionary Items
.........................

.. grid:: 1 1 1 2
    :gutter: 1

    .. grid-item-card:: :bdg-danger:`Avoid`

        .. code-block::

            del d[key]

            d.pop(key)

    .. grid-item-card:: :bdg-info:`Prefer`

        .. code-block::

            {
                k: v
                for k, v in d.items()
                if k != key
            }

            # Better for removing multiple items
            {
                k: d[k]
                for k in set(d).difference([key])
            }

This scenario doesn't come up very frequently. When it does though, the best way to
remove items from dictionaries is to create a copy of the original, but with a filtered
set of keys. One way to do this is with a dictionary comprehension. The example below
shows an interface where you're able to enter a new term and definition. Once added,
you can click a delete button to remove the term and definition:

.. idom:: _examples/dict_remove


Working with Lists
------------------

Below are some ways to update lists without mutating them:

.. card:: Replacing Items
    :link: replacing-list-items
    :link-type: ref

    Avoid using item  or slice assignment. Instead try the strategies below:

    .. code-block::

        l[:index] + [value] + l[index + 1:]

        l[:start] + values + l[end + 1:]

.. card:: Inserting Items
    :link: inserting-list-items
    :link-type: ref

    Avoid using ``list.append``, ``list.extend``, and ``list.insert``. Instead try the
    strategies below:

    .. code-block::

        [*l, value]

        l + [value]

        l + values

        l[:index] + [value] + l[index:]

.. card:: Removing Items
    :link: removing-list-items
    :link-type: ref

    Avoid using item deletion or ``list.pop``. Instead try the strategy below:

    .. code-block::

        l[:index - 1] + l[index:]


..card:: Re-ordering Items
    :link: re-ordering-list-items
    :link-type: ref


    Avoid using ``list.sort`` or ``list.reverse``. Instead try the strategies below:

    .. code-block::

        list(sorted(l))

        list(reversed(l))


.. _replacing-list-items:

Replacing List Items
....................

.. grid:: 1 1 1 2

    .. grid-item-card:: :bdg-danger:`Avoid`

        .. code-block::

            l[index] = value

            l[start:end] = values

    .. grid-item-card:: :bdg-info:`Prefer`

        .. code-block::

            l[:index] + [value] + l[index + 1:]

            l[:start] + values + l[end + 1:]


.. _inserting-list-items:

Inserting List Items
....................

.. grid:: 1 1 1 2

    .. grid-item-card:: :bdg-danger:`Avoid`

        .. code-block::

            l.append(value)

            l.extend(values)

            l.insert(index, value)

    .. grid-item-card:: :bdg-info:`Prefer`

        .. code-block::

            [*l, value]

            l + [value]

            l + values

            l[:index] + [value] + l[index:]


.. _removing-list-items:

Removing List Items
...................

.. grid:: 1 1 1 2

    .. grid-item-card:: :bdg-danger:`Avoid`

        .. code-block::

            del l[index]

            l.pop(index)

    .. grid-item-card:: :bdg-info:`Prefer`

        .. code-block::

            l[:index - 1] + l[index:]


.. _re-ordering-list-items:

Re-ordering List Items
......................

.. grid:: 1 1 1 2

    .. grid-item-card:: :bdg-danger:`Avoid`

        .. code-block::

            l.sort()

            l.reverse()

    .. grid-item-card:: :bdg-info:`Prefer`

        .. code-block::

            list(sorted(l))

            list(reversed(l))


Working with Sets
-----------------

Below are ways to update sets without mutating them:

.. card:: Adding Items
    :link: adding-set-items
    :link-type: ref

    Avoid using item assignment, ``set.add`` or ``set.update``. Instead try the
    strategies below:

    .. code-block::

        s.union({value})

        s.union(values)

.. card:: Removing Items
    :link: removing-set-items
    :link-type: ref

    Avoid using item deletion or ``dict.pop``. Instead try the strategies below:

    .. code-block::

        s.difference({value})

        s.difference(values)

        s.intersection(values)


.. _adding-set-items:

Adding Set Items
................

.. grid:: 1 1 1 2

    .. grid-item-card:: :bdg-danger:`Avoid`

        .. code-block::

            s.add(value)

            s.update(values)

    .. grid-item-card:: :bdg-info:`Prefer`

        .. code-block::

            s.union({value})

            s.union(values)


.. _removing-set-items:

Removing Set Items
..................

.. grid:: 1 1 1 2

    .. grid-item-card:: :bdg-danger:`Avoid`

        .. code-block::

            s.remove(value)

            s.difference_update(values)

            s.intersection_update(values)

    .. grid-item-card:: :bdg-info:`Prefer`

        .. code-block::

            s.difference({value})

            s.difference(values)

            s.intersection(values)


Useful Packages
---------------

