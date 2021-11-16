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
    the server.
