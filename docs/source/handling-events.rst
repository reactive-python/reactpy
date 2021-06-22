Handling Events
===============

When :ref:`Getting Started`, we saw how IDOM makes it possible to write server-side code
that defines basic views and can react to client-side events. The simplest way to listen
and respond to events is by assigning a callable object to a :ref:`VDOM <VDOM Mimetype>`
an attribute where event signals are sent. This is relatively similar to
`handling events in React`_:

.. _handling events in React: https://reactjs.org/docs/handling-events.html

.. example:: show_click_event


Differences With React Events
-----------------------------

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

.. example:: prevent_default_event_actions

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

.. example:: stop_event_propagation


Event Data Serialization
........................

Not all event data is serialized. The most notable example of this is the lack of a
``target`` key in the dictionary sent back to the handler. Instead, data which is not
inherhently JSON serializable must be treated on a case-by-case basis. A simple case
to demonstrate this is the ``currentTime`` attribute of ``audio`` and ``video``
elements. Normally this would be accessible via ``event.target.currenTime``, but here
it's simply passed in under the key ``currentTime``:

.. example:: play_audio_sound
