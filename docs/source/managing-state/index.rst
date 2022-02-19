Managing State
==============

.. toctree::
    :hidden:

    structuring-your-state/index
    shared-component-state/index
    when-and-how-to-reset-state/index

.. dropdown:: :octicon:`bookmark-fill;2em` What You'll Learn
    :color: info
    :animate: fade-in
    :open:

    .. grid:: 1 2 2 2

        .. grid-item-card:: :octicon:`code-square` Structuring Your State
            :link: structuring-your-state/index
            :link-type: doc

            Make it easy to reason about your application by organizing its state.

        .. grid-item-card:: :octicon:`link` Shared Component State
            :link: shared-component-state/index
            :link-type: doc

            Allow components to vary vary together, by lifting state into common
            parents.

        .. grid-item-card:: :octicon:`light-bulb` When and How to Reset State
            :link: when-and-how-to-reset-state/index
            :link-type: doc

            Control if and how state is preserved by understanding it's relationship to
            the "UI tree".


Section 4: Shared Component State
---------------------------------

Sometimes, you want the state of two components to always change together. To do it,
remove state from both of them, move it to their closest common parent, and then pass it
down to them via props. This is known as “lifting state up”, and it’s one of the most
common things you will do writing code with IDOM.

In the example below the search input and the list of elements below share the same
state, the state represents the food name. Note how the component ``Table`` gets called
at each change of state. The component is observing the state and reacting to state
changes automatically, just like it would do in React.

.. idom:: shared-component-state/_examples/synced_inputs

.. card::
    :link: shared-component-state/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Allow components to vary vary together, by lifting state into common parents.
