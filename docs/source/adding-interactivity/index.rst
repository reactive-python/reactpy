Adding Interactivity
====================

.. toctree::
    :hidden:

    responding-to-events/index
    components-with-state/index
    components-sharing-state/index
    state-as-a-snapshot/index
    multiple-state-updates/index
    dangers-of-mutability/index


.. dropdown:: :octicon:`bookmark-fill;2em` What You'll Learn
    :color: info
    :animate: fade-in
    :open:

    .. grid:: 1 2 2 2

        .. grid-item-card:: :octicon:`bell` Responding to Events
            :link: responding-to-events/index
            :link-type: doc

            Define event handlers and learn about the available event types they can be
            bound to.

        .. grid-item-card:: :octicon:`package-dependencies` Components With State
            :link: components-with-state/index
            :link-type: doc

            Allow components to change what they display by saving and updating their
            state.

        .. grid-item-card:: :octicon:`device-camera-video` State as a Snapshot
            :link: state-as-a-snapshot/index
            :link-type: doc

            Learn why state updates schedules a re-render, instead of being applied
            immediately.

        .. grid-item-card:: :octicon:`versions` Multiple State Updates
            :link: multiple-state-updates/index
            :link-type: doc

            Learn how updates to a components state can be batched, or applied
            incrementally.

        .. grid-item-card:: :octicon:`issue-opened` Dangers of Mutability
            :link: dangers-of-mutability/index
            :link-type: doc

            See the pitfalls of working with mutable data types and how to avoid them.


Section 1: Responding to Events
-------------------------------

IDOM lets you add event handlers to your parts of the interface. This means that you can
define synchronous or asynchronous functions that are triggered when a particular user
interaction occurs like clicking, hovering, of focusing on form inputs, and more.

.. idom:: responding-to-events/_examples/button_prints_message

It may feel weird to define a function within a function like this, but doing so allows
the ``handle_event`` function to access information from within the scope of the
component. That's important if you want to use any arguments that may have beend passed
your component in the handler.

.. card::
    :link: responding-to-events/index
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

.. idom:: components-with-state/_examples/adding_state_variable

In IDOM, ``use_state``, as well as any other function whose name starts with ``use``, is
called a "hook". These are special functions that should only be called while IDOM is
:ref:`rendering <the rendering process>`. They let you "hook into" the different
capabilities of IDOM's components of which ``use_state`` is just one (well get into the
other :ref:`later <managing state>`).

.. card::
    :link: components-with-state/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Allow components to change what they display by saving and updating their state.


Section 3: Components Sharing State
-----------------------------------

Sometimes you want the state of two components to always change together. To do it, you
need to be able to share state between those two components, to share state between 
componets move state to the nearest parent. In React world this is known as "lifting
state up" and it is a very common thing to do. Let's look at 2 examples, also from 
`React <https://beta.reactjs.org/learn/sharing-state-between-components>`__, 
but translated to IDOM.

.. idom:: components-sharing-state/_examples/filterable_list


Section 4: State as a Snapshot
------------------------------

As we :ref:`learned earlier <Components with State>`, state setters behave a little
differently than you might exepct at first glance. Instead of updating your current
handle on the setter's corresponding variable, it schedules a re-render of the component
which owns the state.

.. code-block::

    count, set_count = use_state(0)
    print(count)  # prints: 0
    set_count(count + 1)  # schedule a re-render where count is 1
    print(count)  # still prints: 0

This behavior of IDOM means that each render of a component is like taking a snapshot of
the UI based on the component's state at that time. Treating state in this way can help
reduce subtle bugs. For instance, in the code below there's a simple chat app with a
message input and recipient selector. The catch is that the message actually gets sent 5
seconds after the "Send" button is clicked. So what would happen if we changed the
recipient between the time the "Send" button was clicked and the moment the message is
actually sent?

.. idom:: state-as-a-snapshot/_examples/print_chat_message

As it turns out, changing the message recipient after pressing send does not change
where the message ulitmately goes. However, one could imagine a bug where the recipient
of a message is determined at the time the message is sent rather than at the time the
"Send" button it clicked. Thus changing the recipient after pressing send would change
where the message got sent.

In many cases, IDOM avoids this class of bug entirely because it treats state as a
snapshot.

.. card::
    :link: state-as-a-snapshot/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Learn why state updates schedules a re-render, instead of being applied immediately.


Section 5: Multiple State Updates
---------------------------------

As we saw in an earlier example, :ref:`setting state triggers renders`. In other words,
changes to state only take effect in the next render, not in the current one. Further,
changes to state are batched, calling a particular state setter 3 times won't trigger 3
renders, it will only trigger 1. This means that multiple state assignments are batched
- so long as the event handler is synchronous (i.e. the event handler is not an
``async`` function), IDOM waits until all the code in an event handler has run before
processing state and starting the next render:

.. idom:: multiple-state-updates/_examples/set_color_3_times

Sometimes though, you need to update a state variable more than once before the next
render. In these cases, instead of having updates batched, you instead want them to be
applied incrementally. That is, the next update can be made to depend on the prior one.
To accomplish this, instead of passing the next state value directly (e.g.
``set_state(new_state)``), we may pass an **"updater function"** of the form
``compute_new_state(old_state)`` to the state setter (e.g.
``set_state(compute_new_state)``):

.. idom:: multiple-state-updates/_examples/set_state_function

.. card::
    :link: multiple-state-updates/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Learn how updates to a components state can be batched, or applied incrementally.


Section 6: Dangers of Mutability
--------------------------------

While state can hold any type of value, you should be careful to avoid directly
modifying objects that you declare as state with IDOM. In other words, you must not
:ref:`"mutate" <What is a Mutation>` values which are held as state. Rather, to change
these values you should use new ones or create copies.

This is because IDOM does not understand that when a value is mutated, it may have
changed. As a result, mutating values will not trigger re-renders. Thus, you must be
careful to avoid mutation whenever you want IDOM to re-render a component. For example,
instead of mutating dictionaries to update their items you should instead create a
copy that contains the desired changes:

.. idom:: dangers-of-mutability/_examples/dict_update

.. card::
    :link: dangers-of-mutability/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    See the pitfalls of working with mutable data types and how to avoid them.
