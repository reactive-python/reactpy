Sharing Component State
=======================

.. note::

    Parts of this document are still under construction 🚧

Sometimes, you want the state of two components to always change together. To do it,
remove state from both of them, move it to their closest common parent, and then pass it
down to them via props. This is known as “lifting state up”, and it’s one of the most
common things you will do writing code with IDOM.


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
