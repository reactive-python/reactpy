Adding Interactivity
====================

.. toctree::
    :hidden:

    responding-to-events
    components-with-state
    state-as-a-snapshot
    dangers-of-mutability
    batched-updates


.. dropdown:: :octicon:`bookmark-fill;2em` What You'll Learn
    :color: info
    :animate: fade-in
    :open:

    .. grid:: 2

        .. grid-item-card:: :octicon:`bell` Responding to Events
            :link: responding-to-events
            :link-type: doc

            Define event handlers and learn about the available event types they can be
            bound to.

        .. grid-item-card:: :octicon:`package-dependencies` Components With State
            :link: components-with-state
            :link-type: doc

            Allow components to change what they display by saving and updating their
            state.

        .. grid-item-card:: :octicon:`device-camera-video` State as a Snapshot
            :link: state-as-a-snapshot
            :link-type: doc

            Under construction 🚧

        .. grid-item-card:: :octicon:`issue-opened` Dangers of Mutability
            :link: dangers-of-mutability
            :link-type: doc

            Under construction 🚧

        .. grid-item-card:: :octicon:`versions` Batched Updates
            :link: batched-updates
            :link-type: doc

            Under construction 🚧


Section 1: Responding to Events
-------------------------------

IDOM lets you add event handlers to your parts of the interface. This means that you can
define synchronous or asynchronous functions that are triggered when a particular user
interaction occurs like clicking, hovering, of focusing on form inputs, and more.

.. example:: adding_interactivity/button_prints_message
    :activate-result:

It may feel weird to define a function within a function like this, but doing so allows
the ``handle_event`` function to access information from within the scope of the
component. That's important if you want to use any arguments that may have beend passed
your component in the handler.

.. card::
    :link: responding-to-events
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Define event handlers and learn about the available event types they can be bound
    to.


Section 2: Components with State
--------------------------------

Components often need to change what’s on the screen as a result of an interaction. For
example, typing into the form should update the input field, clicking a “Comment” button
should bring up a text input field, clicking “Buy” should put a product in the shopping
cart. Components need to “remember” things like the current input value, the current
image, the shopping cart. In IDOM, this kind of component-specific memory is created and
updated with a "hook" called ``use_state()`` that creates a **state variable** and
**state setter** respectively:

.. example:: adding_interactivity/adding_state_variable
    :activate-result:

In IDOM, ``use_state``, as well as any other function whose name starts with ``use``, is
called a "hook". These are special functions that should only be called while IDOM is
:ref:`rendering <the rendering process>`. They let you "hook into" the different
capabilities of IDOM's components of which ``use_state`` is just one (well get into the
other :ref:`later <managing state>`).

.. card::
    :link: components-with-state
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Allow components to change what they display by saving and updating their state.


Section 3: State as a Snapshot
------------------------------

As we :ref:`learned earlier <Components with State>`, state setters behave a little
differently than you might exepct at first glance. Instead of updating your current
handle on the corresponding state variable it schedules a re-render of the component
which owns the state:

.. code-block::

    print(count)
    set_count(count + 1)
    print(count)

.. card::
    :link: state-as-a-snapshot
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    ...


Section 4: Dangers of Mutability
--------------------------------

.. card::
    :link: dangers-of-mutability
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    ...


Section 3: Batched Updates
--------------------------

.. card::
    :link: batched-updates
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    ...
