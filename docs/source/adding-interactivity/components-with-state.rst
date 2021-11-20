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


Your First Hook
---------------

In IDOM, ``use_state``, as well as any other function whose name starts with ``use``, is
called a "hook". These are special functions that should only be called while IDOM is
:ref:`rendering <the rendering process>`. They let you "hook into" the different
capabilities of IDOM's components of which ``use_state`` is just one (well get into the
other :ref:`later <managing state>`).

While hooks are just normal functions, but it's helpful to think of them as
:ref:`unconditioned <rules of hooks>` declarations about a component's needs. In other
words, you'll "use" hooks at the top of your component in the same way you might
"import" modules at the top of your Python files.


Introduction to ``use_state``
-----------------------------

When you call :func:`~idom.core.hooks.use_state` inside the body of a component's render
function, you're declaring that this component needs to remember something. That
"something" which needs to be remembered, is known as **state**. So when we look at an
assignment expression like the one below

.. code-block::

    index, set_index = use_state(0)

we should read it as saying that ``index`` is a piece of state which must be
remembered by the component that declared it. The argument to ``use_state`` (in this
case ``0``) is then conveying what the initial value for ``index`` is.

We should then understand that each time the component which owns this state renders
``use_state`` will return a tuple containing two values - the current value of the state
(``index``) and a function to change that value the next time the component is rendered.
Thus, in this example:

- ``index`` - is a **state variable** containing the currently stored value.
- ``set_index`` - is a **state setter** for changing that value and triggering a re-render
  of the component.

The convention is that, if you name your state variable ``thing``, your state setter
should be named ``set_thing``. While you could name them anything you want, adhereing to
the convention makes things easier to understand across projects.

----

To understand how this works in context, let's break down our example by examining key
moments in the execution of the ``App`` component. Each numbered tab in the section
below highlights a line of code where something of interest occurs:

.. hint::

    Try clicking through the numbered tabs to each highlighted step of execution

.. tab-set::

    .. tab-item:: 1

        .. raw:: html

            <h2>Initial render</h2>

        .. literalinclude:: /_examples/adding_interactivity/adding_state_variable/app.py
            :lines: 12-33
            :emphasize-lines: 2

        At this point, we've just begun to render the ``App`` component. As yet, IDOM is
        not aware that this component has any state or what view it will display. This
        will change in a moment though when we move to the next line...

    .. tab-item:: 2

        .. raw:: html

            <h2>Initial state declaration</h2>

        .. literalinclude:: /_examples/adding_interactivity/adding_state_variable/app.py
            :lines: 12-33
            :emphasize-lines: 3

        The ``App`` component has just declared some state. IDOM now knows that it must
        remember the ``index`` and trigger an update of this component when
        ``set_index`` is called. Currently the value of ``index`` is ``0`` as per the
        default value given to ``use_state``. Thus, the resulting view will display
        information about the first item in our ``sculpture_data`` list.

    .. tab-item:: 3

        .. raw:: html

            <h2>Define event handler</h2>

        .. literalinclude:: /_examples/adding_interactivity/adding_state_variable/app.py
            :lines: 12-33
            :emphasize-lines: 5

        We've now defined an event handler that we intend to assign to a button in the
        view. This will respond once the user clicks that button. The action this
        handler performs is to update the value of ``index`` and schedule our ``App``
        component to update.

    .. tab-item:: 4

        .. raw:: html

            <h2>Return the view</h2>

        .. literalinclude:: /_examples/adding_interactivity/adding_state_variable/app.py
            :lines: 12-33
            :emphasize-lines: 16

        The ``handle_click`` function we defined above has now been assigned to a button
        in the view and we are about to display information about the first item in out
        ``sculpture_data`` list. When the view is ultimately displayed, if a user clicks
        the "Next" button, the handler we just assigned will be triggered. Until that
        point though, the application will remain static.

    .. tab-item:: 5

        .. raw:: html

            <h2>User interaction</h2>

        .. literalinclude:: /_examples/adding_interactivity/adding_state_variable/app.py
            :lines: 12-33
            :emphasize-lines: 5

        A user has just clicked the button 🖱️! IDOM has sent information about the event
        to the ``handle_click`` function and it is about to execute. In a moment we will
        update the state of this component and schedule a re-render.

    .. tab-item:: 6

        .. raw:: html

            <h2>Event handler triggers</h2>

        .. literalinclude:: /_examples/adding_interactivity/adding_state_variable/app.py
            :lines: 12-33
            :emphasize-lines: 6

        We've just now told IDOM that we want to update the state of our ``App`` and
        that it needs to be re-rendered. More specifically, we are incrementing its
        ``index``, and once ``App`` re-renders the index *will* be ``1``. Importantly,
        at this point, **the value of ``index`` is still ``0``**! This will only change
        once the component begins to re-render.

    .. tab-item:: 7

        .. raw:: html

            <h2>Next render begins</h2>

        .. literalinclude:: /_examples/adding_interactivity/adding_state_variable/app.py
            :lines: 12-33
            :emphasize-lines: 2

        The scheduled re-render of ``App`` has just begun. IDOM has now updated its
        internal state store such that, the next time we call ``use_state`` we will get
        back the updated value of ``index``.

    .. tab-item:: 8

        .. raw:: html

            <h2>Next state is acquired</h2>

        .. literalinclude:: /_examples/adding_interactivity/adding_state_variable/app.py
            :lines: 12-33
            :emphasize-lines: 3

        With IDOM's state store updated, as we call ``use_state``, instead of returning
        ``0`` for the value of ``index`` as it did before, IDOM now returns the value
        ``1``. With this change the view we display will be altered - instead of
        displaying data for the first item in our ``sculpture_data`` list we will now
        display information about the second.

    .. tab-item:: 9

        .. raw:: html

            <h2>Repeat...</h2>

        .. literalinclude:: /_examples/adding_interactivity/adding_state_variable/app.py
            :lines: 12-33

        From this point on, the steps remain the same. The only difference being the
        progressively incrementing ``index`` each time the user clicks the "Next" button
        and the view which is altered to to reflect the currently indexed item in the
        ``sculpture_data`` list.

        .. note::

            Once we reach the end of the ``sculpture_data`` list the view will return
            back to the first item since we create a ``bounded_index`` by doing a modulo
            of the index with the length of the list (``index % len(sculpture_data)``).
            Ideally we would do this bounding at the time we call ``set_index`` to
            prevent ``index`` from incrementing to infinity, but to keep things simple
            in this examples, we've kept this logic separate.

Multiple State Declarations
---------------------------
