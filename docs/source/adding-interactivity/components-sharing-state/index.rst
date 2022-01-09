Components Sharing State
========================

Sometimes you want the state of two components to always change together. To do it, you
need to be able to share state between those two components, to share state between 
componets move state to the nearest parent. In React world this is known as "lifting
state up" and it is a very common thing to do. Let's look at 2 examples, also from 
`React <https://beta.reactjs.org/learn/sharing-state-between-components>`__, 
but translated to IDOM.

Sycned Inputs
-------------

In the code below the two input boxes are syncronized, this happens because they share
state. The state is shared via the parent component ``SyncedInputs``. Check the ``value``
and ``set_value`` variables.

.. code-block::
    :linenos:
    :lineno-start: 14

    from idom import component, html, run, hooks

    @component
    def SyncedInputs():
        value, set_value = hooks.use_state("")
        return html.p(
            Input("First input", value, set_value),
            Input("Second input", value, set_value),
        )


    @component
    def Input(label, value, set_value):
        def handle_change(event):
            set_value(event["target"]["value"])

        return html.label(
            label + " ", html.input({"value": value, "onChange": handle_change})
        )

    run(SyncedInputs)


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
