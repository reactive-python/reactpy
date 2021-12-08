Multiple State Updates
======================

Setting a state variable will queue another render. But sometimes you might want to
perform multiple operations on the value before queueing the next render. To do this, it
helps to understand how React batches state updates.


Batched Updates
---------------

As we learned :ref:`previously <state as a snapshot>`, state variables remain fixed
inside each render as if state were a snapshot taken at the begining of each render.
This is why, in the example below, even though it might seem like clicking the
"Increment" button would cause the ``number`` to increase by ``3``, it only does by
``1``:

.. idom:: _examples/set_counter_3_times

The reason this happens is because, so long as the event handler is synchronous (i.e.
the event handler is not an ``async`` function), IDOM waits until all the code in an
event handler has run before processing state and starting the next render. Thus, it's
the last call to a given state setter that matters. In the example below, even though we
set the color of the button to ``"orange"`` and then ``"pink"`` before ``"blue"``,
the color does not quickly flash orange and pink before blue - it alway remains blue:

.. idom:: _examples/set_color_3_times

This behavior let's you make multiple state changes without triggering unnecessary
renders or renders with inconsistent state where only some of the variables have been
updated. With that said, it also means that the UI won't change until after synchronous
handlers have finished running.

.. note::

    For asynchronous event handlers, IDOM will not render until you ``await`` something.
    As we saw in :ref:`prior examples <State And Delayed Reactions>`, if you introduce
    an asynchronous delay to an event handler after changing state, renders may take
    place before the remainder of the event handler completes. However, state variables
    within handlers, even async ones, always remains static.

This behavior of IDOM to "batch" state changes that take place inside a single event
handler, do not extend across event handlers. In other words, distinct events will
always produce distinct renders. For example, if clicking a button increments a counter
by one, no matter how fast the user clicks, the view will never jump from 1 to 3 - it
will always display 1, then 2, and then 3.


Incremental Updates
-------------------

While it's uncommon, you need to update a state variable more than once before the next
render. In these cases, instead of having updates batched, you instead want them to be
applied incrementally. That is, the next update can be made to depend on the prior one.
For example, what it we wanted to make it so that, in our ``Counter`` example :ref:`from
before <Batched Updates>`, each call to ``set_number`` did in fact increment
``number`` by one causing the view to display ``0``, then ``3``, then ``6``, and so on?

To accomplish this, instead of passing the next state value as in ``set_number(number +
1)``, we may pass an **"updater function"** to ``set_number`` that computes the next
state based on the previous state. This would look like ``set_number(lambda number:
number + 1)``. In other words we need a function of the form:

.. code-block::

    def compute_new_state(old_state):
        ...
        return new_state

In our case, ``new_state = old_state + 1``. So we might define:

.. code-block::

    def increment(old_number):
        new_number = old_number + 1
        return new_number

Which we can use to replace ``set_number(number + 1)`` with ``set_number(increment)``:

.. idom:: _examples/set_state_function

The way to think about how IDOM runs though this series of ``set_state(increment)``
calls is to imagine that each one updates the internally managed state with its return
value, then that return value is being passed to the next updater function. Ultimately,
this is functionally equivalent to the following:

.. code-block::

    set_number(increment(increment(increment(number))))

So why might you want to do this? Why not just compute ``set_number(number + 3)`` from
the start? The easiest way to explain the use case is with an example. Imagine that we
introduced a delay before ``set_number(number + 1)``. What would happen if we clicked
the "Increment" button more than once before the delay in the first triggered event
completed?

.. idom:: _examples/delay_before_set_count

From an :ref:`earlier lesson <State And Delayed Reactions>`, we learned that introducing
delays do not change the fact that state variables do not change until the next render.
As a result, despite clicking many times before the delay completes, the ``number`` only
increments by one. To solve this we can use updater functions:

.. idom:: _examples/delay_before_count_updater

Now when you click the "Increment" button, each click, though delayed, corresponds to
``number`` being increased. This is because the ``old_number`` in the updater function
uses the value which was assigned by the last call to ``set_number`` rather than relying
in the static ``number`` state variable.
