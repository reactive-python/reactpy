Managing State
==============

.. toctree::
    :hidden:

    how-to-structure-state/index
    sharing-component-state/index
    when-and-how-to-reset-state/index
    simplifying-updates-with-reducers/index
    deeply-sharing-state-with-contexts/index
    combining-contexts-and-reducers/index

.. dropdown:: :octicon:`bookmark-fill;2em` What You'll Learn
    :color: info
    :animate: fade-in
    :open:

    .. grid:: 1 2 2 2

        .. grid-item-card:: :octicon:`organization` How to Structure State
            :link: how-to-structure-state/index
            :link-type: doc

            Make it easy to reason about your application with strategies for organizing
            state.

        .. grid-item-card:: :octicon:`link` Sharing Component State
            :link: sharing-component-state/index
            :link-type: doc

            Allow components to vary vary together, by lifting state into common
            parents.

        .. grid-item-card:: :octicon:`light-bulb` When and How to Reset State
            :link: when-and-how-to-reset-state/index
            :link-type: doc

            Control if and how state is preserved by understanding it's relationship to
            the "UI tree".

        .. grid-item-card:: :octicon:`plug` Simplifying Updates with Reducers
            :link: simplifying-updates-with-reducers/index
            :link-type: doc

            Consolidate state update logic outside your component in a single function,
            called a “reducer".

        .. grid-item-card:: :octicon:`broadcast` Deeply Sharing State with Contexts
            :link: deeply-sharing-state-with-contexts/index
            :link-type: doc

            Instead of passing shared state down deep component trees, bring state into
            "contexts" instead.

        .. grid-item-card:: :octicon:`rocket` Combining Contexts and Reducers
            :link: combining-contexts-and-reducers/index
            :link-type: doc

            You can combine reducers and context together to manage state of a complex
            screen.


Section 1: How to Structure State
---------------------------------

.. note::

    Under construction 🚧


Section 2: Shared Component State
---------------------------------

Sometimes, you want the state of two components to always change together. To do it,
remove state from both of them, move it to their closest common parent, and then pass it
down to them via props. This is known as “lifting state up”, and it’s one of the most
common things you will do writing code with ReactPy.

In the example below the search input and the list of elements below share the same
state, the state represents the food name. Note how the component ``Table`` gets called
at each change of state. The component is observing the state and reacting to state
changes automatically, just like it would do in React.

.. reactpy:: sharing-component-state/_examples/synced_inputs

.. card::
    :link: sharing-component-state/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Allow components to vary vary together, by lifting state into common parents.


Section 3: When and How to Reset State
--------------------------------------

.. note::

    Under construction 🚧


Section 4: Simplifying Updates with Reducers
--------------------------------------------

.. note::

    Under construction 🚧


Section 5: Deeply Sharing State with Contexts
---------------------------------------------

.. note::

    Under construction 🚧



Section 6: Combining Contexts and Reducers
------------------------------------------

.. note::

    Under construction 🚧
