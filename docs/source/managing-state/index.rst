Managing State
==============

.. toctree::
    :hidden:

    keeping-components-pure
    logical-flow-of-state
    structuring-your-state
    shared-component-state/index
    when-to-reset-state
    writing-tests



Section 4: Shared Component State
---------------------------------

Sometimes you want the state of two components to always change together. To do it, you
need to be able to share state between those two components, to share state between 
componets move state to the nearest parent. In React world this is known as "lifting
state up" and it is a very common thing to do. Let's look at 2 examples, also from 
`React <https://beta.reactjs.org/learn/sharing-state-between-components>`__, 
but translated to IDOM.