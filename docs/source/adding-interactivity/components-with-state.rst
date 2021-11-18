Components With State
=====================

Components often need to change what’s on the screen as a result of an interaction. For
example, typing into the form should update the input field, clicking “next” on an image
carousel should change which image is displayed, clicking “buy” should put a product in
the shopping cart. Components need to “remember” things: the current input value, the
current image, the shopping cart. In IDOM, this kind of component-specific memory is
called state.


When Variables Aren't Enough
----------------------------

Below is a gallery of images about sculpture. Clicking the "Next" button should
increment the ``index`` and, as a result, change what image is displayed. However, this
does not work:

.. example:: adding_interactivity.when_variables_arent_enough
    :activate-result:

.. note::

    Try clicking the button to see that it does not cause a change.

After clicking "Next", if you check the server logs, you'll discover an
``UnboundLocalError`` error. It turns out that in this case, the ``index = index + 1``
statement is similar to `trying to set global variables
<https://stackoverflow.com/questions/9264763/dont-understand-why-unboundlocalerror-occurs-closure>`__.
Tehcnically there's a way to `fix this error
<https://docs.python.org/3/reference/simple_stmts.html#nonlocal>`__, but even if we did,
that still wouldn't fix the underlying problems:

1. **Local variables do not persist across component renders** - when a component is
   updated, its associated function gets called again. That is, it renders. As a result,
   all the local state that was created the last time the function was called gets
   destroyed when it updates.

2. **Changes to local variables do not cause components to re-render** - there's no way
   for IDOM to observe when these variables change. Thus IDOM is not aware that
   something has changed and that a re-render should take place.

To address these problems, IDOM provides the :func:`~idom.core.hooks.use_state` "hook"
which provides:

1. A **state variable** whose data is retained aross renders.

2. A **state setter** function that can be used to update that variable and trigger a
   render.


Adding State to Components
--------------------------

To use the ``use_state()`` hook to create a state variable and setter in the
:ref:`example above <When Variables Aren't Enough>` we'll first import it:

.. testcode::

    from idom import use_state

Then we'll make the following changes to our code from before:

.. code-block:: diff

    -    index = 0
    +    index, set_index = use_state

         def handle_click(event):
    -        index = index + 1
    +        set_index(index + 1)

After making those changes we should get:

.. code-block::
    :linenos:
    :lineno-start: 14

        index, set_index = use_state(0)

        def handle_click(event):
            set_index(index + 1)

We'll talk more about what this is doing :ref:`shortly <your first hook>`, but for
now let's just verify that this does in fact fix the problems from before:

.. example:: adding_interactivity.adding_state_variable
    :activate-result:

.. _Your first hook:

.. dropdown:: :octicon:`light-bulb;2em` Your first hook
    :color: warning
    :open:

    In IDOM, ``use_state``, as well as any other function whose name starts with
    ``use``, is called a "hook". These are special functions that should only be called
    while IDOM is :ref:`rendering <the-rendering-process>`. They let you "hook into" the
    different capabilities of IDOM's components of which ``use_state`` is just one (well
    get into the other :ref:`later <managing state>`).

    While hooks are just normal functions, but it's helpful to think of them as
    :ref:`unconditioned <rules of hooks>` declarations about a component's needs. In
    other words, you'll "use" hooks at the top of your component in the same way you
    might "import" modules at the top of your Python files.


Anatomy of ``use_state``
------------------------


Multiple State Declarations
---------------------------
