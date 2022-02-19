Shared Component State
======================


Sometimes you want the state of two components to always change together. To do it, you
need to be able to share state between those two components, to share state between
components move state to the nearest parent. In React world this is known as "lifting
state up" and it is a very common thing to do. Let's look at 2 examples, also from
`React <https://beta.reactjs.org/learn/sharing-state-between-components>`__,
but translated to IDOM.

Synced Inputs
-------------

In the code below the two input boxes are synchronized, this happens because they share
state. The state is shared via the parent component ``SyncedInputs``. Check the ``value``
and ``set_value`` variables.

.. idom:: _examples/synced_inputs

Filterable  List
----------------

In the example below the search input and the list of elements below share the
same state, the state represents the food name.

Note how the component ``Table`` gets called at each change of state. The
component is observing the state and reacting to state changes automatically,
just like it would do in React.

.. idom:: _examples/filterable_list

.. note::

    Try typing a food name in the search bar.
