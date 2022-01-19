Rendering Data
==============

Frequently you need to construct a number of similar components from a collection of
data. Let's imagine that we want to create a todo list that can be ordered and filtered
on the priority of each item in the list. To start, we'll take a look at the kind of
view we'd like to display:

.. code-block:: html

    <ul>
        <li>Make breakfast (important)</li>
        <li>Feed the dog (important)</li>
        <li>Do laundry</li>
        <li>Go on a run (important)</li>
        <li>Clean the house</li>
        <li>Go to the grocery store</li>
        <li>Do some coding</li>
        <li>Read a book (important)</li>
    </ul>

Based on this, our next step in achieving our goal is to break this view down into the
underlying data that we'd want to use to represent it. The most straightforward way to
do this would be to just put the text of each ``<li>`` into a list:

.. testcode::

    tasks = [
        "Make breakfast (important)",
        "Feed the dog (important)",
        "Do laundry",
        "Go on a run (important)",
        "Clean the house",
        "Go to the grocery store",
        "Do some coding",
        "Read a book (important)",
    ]

We could then take this list and "render" it into a series of ``<li>`` elements:

.. testcode::

    from idom import html

    list_item_elements = [html.li(text) for text in tasks]

This list of elements can then be passed into a parent ``<ul>`` element:

.. testcode::

    list_element = html.ul(list_item_elements)

The last thing we have to do is return this from a component:

.. idom:: _examples/todo_from_list


Filtering and Sorting Elements
------------------------------

Our representation of ``tasks`` worked fine to just get them on the screen, but it
doesn't extend well to the case where we want to filter and order them based on
priority. Thus, we need to change the data structure we're using to represent our tasks:

.. testcode::

    tasks = [
        {"text": "Make breakfast", "priority": 0},
        {"text": "Feed the dog", "priority": 0},
        {"text": "Do laundry", "priority": 2},
        {"text": "Go on a run", "priority": 1},
        {"text": "Clean the house", "priority": 2},
        {"text": "Go to the grocery store", "priority": 2},
        {"text": "Do some coding", "priority": 1},
        {"text": "Read a book", "priority": 1},
    ]

With this we can now imaging writing some filtering and sorting logic using Python's
:func:`filter` and :func:`sorted` functions respecitvely. We'll do this by only
displaying items whose ``priority`` is less than or equal to some ``filter_by_priority``
and then ordering the elements based on the ``priority``:

.. testcode::

    x = 1

.. testcode::

    filter_by_priority = 1
    sort_by_priority = True

    filtered_tasks = tasks
    if filter_by_priority is not None:
        filtered_tasks = [t for t in filtered_tasks if t["priority"] <= filter_by_priority]
    if sort_by_priority:
        filtered_tasks = list(sorted(filtered_tasks, key=lambda t: t["priority"]))

    assert filtered_tasks == [
        {'text': 'Make breakfast', 'priority': 0},
        {'text': 'Feed the dog', 'priority': 0},
        {'text': 'Go on a run', 'priority': 1},
        {'text': 'Do some coding', 'priority': 1},
        {'text': 'Read a book', 'priority': 1},
    ]

We could then add this code to our ``DataList`` component:

.. idom:: _examples/sorted_and_filtered_todo_list


Organizing Items With Keys
--------------------------

If you run the examples above :ref:`in debug mode <Running IDOM in Debug Mode>` you'll
see the server log a bunch of errors that look something like:

.. code-block:: text

    Key not specified for child in list {'tagName': 'li', 'children': ...}

What this is telling you is that we haven't specified a unique ``key`` for each of the
items in our todo list. In order to silence this warning we need to expand our data
structure even further to include a unique ID for each item in our todo list:

.. testcode::

    tasks = [
        {"id": 0, "text": "Make breakfast", "priority": 0},
        {"id": 1, "text": "Feed the dog", "priority": 0},
        {"id": 2, "text": "Do laundry", "priority": 2},
        {"id": 3, "text": "Go on a run", "priority": 1},
        {"id": 4, "text": "Clean the house", "priority": 2},
        {"id": 5, "text": "Go to the grocery store", "priority": 2},
        {"id": 6, "text": "Do some coding", "priority": 1},
        {"id": 7, "text": "Read a book", "priority": 1},
    ]

Then, as we're constructing our ``<li>`` elements we'll pass in a ``key`` argument to
the element constructor:

.. code-block::

    list_item_elements = [html.li(t["text"], key=t["id"]) for t in tasks]

This ``key`` tells IDOM which ``<li>`` element corresponds to which item of data in our
``tasks`` list. This becomes important if the order or number of items in your list can
change. In our case, if we decided to change whether we want to ``filter_by_priority``
or ``sort_by_priority`` the items in our ``<ul>`` element would change. Given this,
here's how we'd change our component:

.. idom:: _examples/todo_list_with_keys


Keys for Components
...................

Thus far we've been talking about passing keys to standard HTML elements. However, this
principle also applies to components too. Every function decorated with the
``@component`` decorator automatically gets a ``key`` parameter that operates in the
exact same way that it does for standard HTML elements:

.. testcode::

    from idom import component


    @component
    def ListItem(text):
        return html.li(text)

    tasks = [
        {"id": 0, "text": "Make breakfast"},
        {"id": 1, "text": "Feed the dog"},
        {"id": 2, "text": "Do laundry"},
        {"id": 3, "text": "Go on a run"},
        {"id": 4, "text": "Clean the house"},
        {"id": 5, "text": "Go to the grocery store"},
        {"id": 6, "text": "Do some coding"},
        {"id": 7, "text": "Read a book"},
    ]

    list_element = [ListItem(t["text"], key=t["id"]) for t in tasks]


.. warning::

    The ``key`` argument is reserved for this purpose. Defining a component with a
    function that has a ``key`` parameter will cause an error:

    .. testcode::

        from idom import component

        @component
        def FunctionWithKeyParam(key):
            ...

    .. testoutput::

        Traceback (most recent call last):
        ...
        TypeError: Component render function ... uses reserved parameter 'key'


Rules of Keys
.............

In order to avoid unexpected behaviors when rendering data with keys, there are a few
rules that need to be followed. These will ensure that each item of data is associated
with the correct UI element.

.. dropdown:: Keys may be the same if their elements are not siblings
    :color: info

    If two elements have different parents in the UI, they can use the same keys.

    .. testcode::

        data_1 = [
            {"id": 1, "text": "Something"},
            {"id": 2, "text": "Something else"},
        ]

        data_2 = [
            {"id": 1, "text": "Another thing"},
            {"id": 2, "text": "Yet another thing"},
        ]

        html.section(
            html.ul([html.li(data["text"], key=data["id"]) for data in data_1]),
            html.ul([html.li(data["text"], key=data["id"]) for data in data_2]),
        )

.. dropdown:: Keys must be unique amonst siblings
    :color: danger

    Keys must be unique among siblings.

    .. testcode::

        data = [
            {"id": 1, "text": "Something"},
            {"id": 2, "text": "Something else"},
            {"id": 1, "text": "Another thing"},      # BAD: has a duplicated id
            {"id": 2, "text": "Yet another thing"},  # BAD: has a duplicated id
        ]

        html.section(
            html.ul([html.li(data["text"], key=data["id"]) for data in data]),
        )

.. dropdown:: Keys must be fixed to their data.
    :color: danger

    Don't generate random values for keys to avoid the warning.

    .. testcode::

        from random import random

        data = [
            {"id": random(), "text": "Something"},
            {"id": random(), "text": "Something else"},
            {"id": random(), "text": "Another thing"},
            {"id": random(), "text": "Yet another thing"},
        ]

        html.section(
            html.ul([html.li(data["text"], key=data["id"]) for data in data]),
        )

    Doing so will result in unexpected behavior.

Since we've just been working with a small amount of sample data thus far, it was easy
enough for us to manually add an ``id`` key to each item of data. Often though, we have
to work with data that already exists. In those cases, how should we pick what value to
use for each ``key``?

- If your data comes from your database you should use the keys and IDs generated by
  that database since these are inherently unique. For example, you might use the
  primary key of records in a relational database.

- If your data is generated and persisted locally (e.g. notes in a note-taking app), use
  an incrementing counter or :mod:`uuid` from the standard library when creating items.


----------


.. card::
    :link: /understanding-idom/why-idom-needs-keys
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Learn about why IDOM needs keys in the first place.
