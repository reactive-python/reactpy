=========
Hooks API
=========

Hooks are functions that allow you to "hook into" the life cycle events and state of
Components. Their usage should always follow the :ref:`Rules of Hooks`. For most use
cases the :ref:`Basic Hooks` should be enough, however the remaining
:ref:`Supplementary Hooks` should fulfill less common scenarios.


Basic Hooks
===========


Use State
---------

.. code-block::

    state, set_state = use_state(initial_state)

Returns a stateful value and a function to update it.

During the first render the ``state`` will be identical to the ``initial_state`` passed
as the first argument. However in subsequent renders ``state`` will take on the value
passed to ``set_state``.

.. code-block::

    set_state(new_state)

The ``set_state`` function accepts a ``new_state`` as its only argument and schedules a
re-render of the component where ``use_state`` was initially called. During these
subsequent re-renders the ``state`` returned by ``use_state`` will take on the value
of ``new_state``.

.. note::

    The identity of ``set_state`` is guaranteed to be preserved across renders. This
    means it can safely be omitted from dependency lists in :ref:`Use Effect` or
    :ref:`Use Callback`.


Functional Updates
..................

If the new state is computed from the previous state, you can pass a function which
accepts a single argument (the previous state) and returns the next state. Consider this
simply use case of a counter where we've pulled out logic for increment and
decremented the count:

.. idom:: _examples/use_state_counter

We use the functional form for the "+" and "-" buttons since the next ``count`` depends
on the previous value, while for the "Reset" button we simple assign the
``initial_count`` since it is independent of the prior ``count``. This is a trivial
example, but it demonstrates how complex state logic can be factored out into well
defined and potentially reusable functions.


Lazy Initial State
..................

In cases where it is costly to create the initial value for ``use_state``, you can pass
a constructor function that accepts no arguments instead - it will be called on the
first render of a component, but will be disregarded in all following renders:

.. code-block::

    state, set_state = use_state(lambda: some_expensive_computation(a, b, c))


Skipping Updates
................

If you update a State Hook to the same value as the current state then the component which
owns that state will not be rendered again. We check ``if new_state is current_state``
in order to determine whether there has been a change. Thus the following would not
result in a re-render:

.. code-block::

    state, set_state = use_state([])
    set_state(state)


Use Effect
----------

.. code-block::

    use_effect(did_render)

The ``use_effect`` hook accepts a function which may be imperative, or mutate state. The
function will be called immediately after the layout has fully updated.

Asynchronous actions, mutations, subscriptions, and other `side effects`_ can cause
unexpected bugs if placed in the main body of a component's render function. Thus the
``use_effect`` hook provides a way to safely escape the purely functional world of
component render functions.

.. note::

    Normally in React the ``did_render`` function is called once an update has been
    committed to the screen. Since no such action is performed by IDOM, and the time
    at which the update is displayed cannot be known we are unable to achieve parity
    with this behavior.


Cleaning Up Effects
...................

If the effect you wish to enact creates resources, you'll probably need to clean them
up. In such cases you may simply return a function that addresses this from the
``did_render`` function which created the resource. Consider the case of opening and
then closing a connection:

.. code-block::

    def establish_connection():
        connection = open_connection()
        return lambda: close_connection(connection)

    use_effect(establish_connection)

The clean-up function will be run before the component is unmounted or, before the next
effect is triggered when the component re-renders. You can
:ref:`conditionally fire events <Conditional Effects>` to avoid triggering them each
time a component renders.


Conditional Effects
...................

By default, effects are triggered after every successful render to ensure that all state
referenced by the effect is up to date. However, when an effect function references
non-global variables, the effect will only if the value of that variable changes. For
example, imagine that we had an effect that connected to a ``url`` state variable:

.. code-block::

    url, set_url = use_state("https://example.com")

    def establish_connection():
        connection = open_connection(url)
        return lambda: close_connection(connection)

    use_effect(establish_connection)

Here, a new connection will be established whenever a new ``url`` is set.


Async Effects
.............

A behavior unique to IDOM's implementation of ``use_effect`` is that it natively
supports ``async`` functions:

.. code-block::

    async def non_blocking_effect():
        resource = await do_something_asynchronously()
        return lambda: blocking_close(resource)

    use_effect(non_blocking_effect)


There are **three important subtleties** to note about using asynchronous effects:

1. The cleanup function must be a normal synchronous function.

2. Asynchronous effects which do not complete before the next effect is created
   following a re-render will be cancelled. This means an
   :class:`~asyncio.CancelledError` will be raised somewhere in the body of the effect.

3. An asynchronous effect may occur any time after the update which added this effect
   and before the next effect following a subsequent update.


Manual Effect Conditions
........................

In some cases, you may want to explicitly declare when an effect should be triggered.
You can do this by passing ``dependencies`` to ``use_effect``. Each of the following
values produce different effect behaviors:

- ``use_effect(..., dependencies=None)`` - triggers and cleans up on every render.
- ``use_effect(..., dependencies=[])`` - only triggers on the first and cleans up after
  the last render.
- ``use_effect(..., dependencies=[x, y])`` - triggers on the first render and on subsequent renders if
  ``x`` or ``y`` have changed.


Use Context
-----------

.. code-block::

    value = use_context(MyContext)

Accepts a context object (the value returned from
:func:`idom.core.hooks.create_context`) and returns the current context value for that
context. The current context value is determined by the ``value`` argument passed to the
nearest ``MyContext`` in the tree.

When the nearest <MyContext.Provider> above the component updates, this Hook will
trigger a rerender with the latest context value passed to that MyContext provider. Even
if an ancestor uses React.memo or shouldComponentUpdate, a rerender will still happen
starting at the component itself using useContext.


Supplementary Hooks
===================


Use Reducer
-----------

.. code-block::

    state, dispatch_action = use_reducer(reducer, initial_state)

An alternative and derivative of :ref:`Use State` the ``use_reducer`` hook, instead of
directly assigning a new state, allows you to specify an action which will transition
the previous state into the next state. This transition is defined by a reducer function
of the form ``(current_state, action) -> new_state``. The ``use_reducer`` hook then
returns the current state and a ``dispatch_action`` function that accepts an ``action``
and causes a transition to the next state via the ``reducer``.

``use_reducer`` is generally preferred to ``use_state`` if logic for transitioning from
one state to the next is especially complex or involves nested data structures.
``use_reducer`` can also be used to collect several ``use_state`` calls together - this
may be slightly more performant as well as being preferable since there is only one
``dispatch_action`` callback versus the many ``set_state`` callbacks.

We can rework the :ref:`Functional Updates` counter example to use ``use_reducer``:

.. idom:: _examples/use_reducer_counter

.. note::

    The identity of the ``dispatch_action`` function is guaranteed to be preserved
    across re-renders throughout the lifetime of the component. This means it can safely
    be omitted from dependency lists in :ref:`Use Effect` or :ref:`Use Callback`.


Use Callback
------------

.. code-block::

    memoized_callback = use_callback(lambda: do_something(a, b))

A derivative of :ref:`Use Memo`, the ``use_callback`` hook returns a
`memoized <memoization>`_ callback. This is useful when passing callbacks to child
components which check reference equality to prevent unnecessary renders. The
``memoized_callback`` will only change when any local variables is references do.

.. note::

    You may manually specify what values the callback depends on in the :ref:`same way
    as effects <Manual Effect Conditions>` using the ``dependencies`` parameter.


Use Memo
--------

.. code-block::

    memoized_value = use_memo(lambda: compute_something_expensive(a, b))

Returns a `memoized <memoization>`_ value. By passing a constructor function accepting
no arguments and an array of dependencies for that constructor, the ``use_callback``
hook will return the value computed by the constructor. The ``memoized_value`` will only
be recomputed if a local variable referenced by the constructor changes (e.g. ``a`` or
``b`` here). This optimizes performance because you don't need to
``compute_something_expensive`` on every render.

Unlike ``use_effect`` the constructor function is called during each render (instead of
after) and should not incur side effects.

.. warning::

    Remember that you shouldn't optimize something unless you know it's a performance
    bottleneck. Write your code without ``use_memo`` first and then add it to targeted
    sections that need a speed-up.

.. note::

    You may manually specify what values the callback depends on in the :ref:`same way
    as effects <Manual Effect Conditions>` using the ``dependencies`` parameter.


Use Ref
-------

.. code-block::

    ref_container = use_ref(initial_value)

Returns a mutable :class:`~idom.utils.Ref` object that has a single
:attr:`~idom.utils.Ref.current` attribute that at first contains the ``initial_state``.
The identity of the ``Ref`` object will be preserved for the lifetime of the component.

A ``Ref`` is most useful if you need to incur side effects since updating its
``.current`` attribute doesn't trigger a re-render of the component. You'll often use this
hook alongside :ref:`Use Effect` or in response to component event handlers.


.. links
.. =====

.. _React Hooks: https://reactjs.org/docs/hooks-reference.html
.. _side effects: https://en.wikipedia.org/wiki/Side_effect_(computer_science)
.. _memoization: https://en.wikipedia.org/wiki/Memoization


Rules of Hooks
==============

Hooks are just normal Python functions, but there's a bit of magic to them, and in order
for that magic to work you've got to follow two rules. Thankfully we supply a
:ref:`Flake8 Plugin` to help enforce them.


Only call outside flow controls
-------------------------------

**Don't call hooks inside loops, conditions, or nested functions.** Instead you must
always call hooks at the top level of your functions. By adhering to this rule you
ensure that hooks are always called in the exact same order. This fact is what allows
IDOM to preserve the state of hooks between multiple calls to ``useState`` and
``useEffect`` calls.


Only call in render functions
-----------------------------

**Don't call hooks from regular Python functions.** Instead you should:

- ✅ Call Hooks from a component's render function.

- ✅ Call Hooks from another custom hook

Following this rule ensures stateful logic for IDOM component is always clearly
separated from the rest of your codebase.


Flake8 Plugin
-------------

We provide a Flake8 plugin called `flake8-idom-hooks <Flake8 Linter Plugin>`_ that helps
to enforce the two rules described above. You can ``pip`` install it directly, or with
the ``lint`` extra for IDOM:

.. code-block:: bash

    pip install flake8-idom-hooks

Once installed running, ``flake8`` on your code will start catching errors. For example:

.. code-block:: bash

    flake8 my_idom_components.py

Might produce something like the following output:

.. code-block:: text

    ./my_idom_components:10:8 ROH102 hook 'use_effect' used inside if statement
    ./my_idom_components:23:4 ROH102 hook 'use_state' used outside component or hook definition

See the Flake8 docs for
`more info <https://flake8.pycqa.org/en/latest/user/configuration.html>`__.

.. links
.. =====

.. _Flake8 Linter Plugin: https://github.com/idom-team/flake8-idom-hooks
