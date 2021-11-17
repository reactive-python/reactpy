Responding to Events
====================

IDOM lets you add event handlers to your parts of the interface. This means that you can
assign functions that are triggered when a particular user interaction occurs like
clicking, hovering, of focusing on form inputs, and more.


Adding Event Handlers
---------------------

To start out we'll just display a button that, for the moment, doesn't do anything:

.. example:: adding_interactivity.button_does_nothing
    :activate-result:

To add an event handler to this button we'll do three things:

1. Declare a function called ``handle_event(event)`` inside the body of our ``Button`` component
2. Add logic to ``handle_event`` that will print the ``event`` it receives to the console.
3. Add an ``"onClick": handle_event`` attribute to the ``<button>`` element.

.. example:: adding_interactivity.button_prints_event
    :activate-result:

.. note::

    Normally print statements will only be displayed in the terminal where you launched
    IDOM.

It may feel weird to define a function within a function like this, but doing so allows
the ``handle_event`` function to access information from within the scope of the
component. That's important if you want to use any arguments that may have beend passed
your component in the handler:

.. example:: adding_interactivity.button_prints_message
    :activate-result:

With all that said, since our ``handle_event`` function isn't doing that much work, if
we wanted to streamline our component definition, we could pass in our event handler as a
lambda:

.. code-block::

    html.button({"onClick": lambda event: print(message_text)}, "Click me!")


Supported Event Types
---------------------

Since IDOM's event information comes from React, most the the information (:ref:`with
some exceptions <event data Serialization>`) about how React handles events translates
directly to IDOM. Follow the links below to learn about each category of event:

- :ref:`Clipboard Events`
- :ref:`Composition Events`
- :ref:`Keyboard Events`
- :ref:`Focus Events`
- :ref:`Form Events`
- :ref:`Generic Events`
- :ref:`Mouse Events`
- :ref:`Pointer Events`
- :ref:`Selection Events`
- :ref:`Touch Events`
- :ref:`UI Events`
- :ref:`Wheel Events`
- :ref:`Media Events`
- :ref:`Image Events`
- :ref:`Animation Events`
- :ref:`Transition Events`
- :ref:`Other Events`


Passing Handlers to Components
------------------------------

A common pattern when factoring out common logic is to pass event handlers into a more
generic component definition. This allows the component to focus on the things which are
common while still giving its usages customizablity. Consider the case below where we
want to create a generic ``Button`` component that can be used for a variety of purpose:

.. example:: adding_interactivity.button_handler_as_arg
    :activate-result:


Async Event Handlers
--------------------

Sometimes event handlers need to execute asynchronous tasks when they are triggered.
Behind the scenes, IDOM is running an :mod:`asyncio` event loop for just this purpose.
By defining your event handler as an asynchronous function instead of a normal
synchronous one. In the layout below we sleep for several seconds before printing out a
message in the first button. However, because the event handler is asynchronous, the
handler for the second button is still able to respond:

.. example:: adding_interactivity.button_async_handlers
    :activate-result:


Event Data Serialization
------------------------

Not all event data is serialized. The most notable example of this is the lack of a
``target`` key in the dictionary sent back to the handler. Instead, data which is not
inherhently JSON serializable must be treated on a case-by-case basis. A simple case
to demonstrate this is the ``currentTime`` attribute of ``audio`` and ``video``
elements. Normally this would be accessible via ``event.target.currenTime``, but here
it's simply passed in under the key ``currentTime``:

.. example:: adding_interactivity.audio_player
    :activate-result:


Client-side Event Behavior
--------------------------

Because IDOM operates server-side, there are inevitable limitations that prevent it from
achieving perfect parity with all the behaviors of React. With that said, any feature
that cannot be achieved in Python with IDOM, can be done by creating
:ref:`Custom Javascript Components`.


Preventing Default Event Actions
................................

Instead of calling an ``event.preventDefault()`` method as you would do in React, you
must declare whether to prevent default behavior ahead of time. This can be accomplished
using the :func:`~idom.core.events.event` decorator and setting ``prevent_default``. For
example, we can stop a link from going to the specified URL:

.. example:: adding_interactivity.prevent_default_event_actions
    :activate-result:

Unfortunately this means you cannot conditionally prevent default behavior in response
to event data without writing :ref:`Custom Javascript Components`.


Stop Event Propogation
......................

Similarly to :ref:`preventing default behavior <Preventing Default Event Actions>`, you
can use the :func:`~idom.core.events.event` decorator to forward declare whether or not
you want events from a child element propogate up through the document to parent
elements by setting ``stop_propagation``. In the example below we place a red ``div``
inside a parent blue ``div``. When propogation is turned on, clicking the red element
will cause the handler for the outer blue one to fire. Conversely, when it's off, only
the handler for the red element will fire.

.. example:: adding_interactivity.stop_event_propagation
    :activate-result:
