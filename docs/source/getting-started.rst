Getting Started
===============

Let's look at the example that you may have seen
:ref:`at a glance <At a Glance>` on the homepage:

.. example:: slideshow
    :linenos:

Since it's likely a lot to take in at once, we'll break it down piece by piece:

.. literalinclude:: /examples/slideshow.py
    :lineno-start: 4
    :lines: 4-5
    :linenos:

The ``idom.component`` decorator creates a :ref:`Component <Stateful Components>`
constructor which is "rendered" by the function below it. To create a Component instance
we call ``Slideshow()`` with the same arguments as its render function. The render
function of a Component returns a data structure that depicts a user interface, or in
more technical terms a Document Object Model (DOM). We call this structural
representation of the DOM a `Virtual DOM`__ (VDOM) - a term familiar to those who work
with `ReactJS`_. In the case of ``Slideshow`` it will return a VDOM representing an
image which, when clicked, will change.

__ https://reactjs.org/docs/faq-internals.html#what-is-the-virtual-dom

.. literalinclude:: /examples/slideshow.py
    :lineno-start: 6
    :lines: 6
    :linenos:

The :func:`~idom.core.hooks.use_state` function is a :ref:`Hook <Life Cycle Hooks>`.
Calling a Hook inside a Component's render function (one decorated by ``idom.component``)
adds some local state to it. IDOM will preserve the state added by Hooks between calls
to the Component's render function.

The ``use_state`` hook returns two values - the *current* state value and a function
that let's you update that value. In the case of ``Slideshow`` the value of the
``use_state`` hook determines which image is showm to the user, while its update
function allow us to change it. The one required argument of ``use_state`` is the
*initial* state value.

.. literalinclude:: /examples/slideshow.py
    :lineno-start: 8
    :lines: 8,9
    :linenos:

The coroutine above will get added as an event handler to the resulting view. When it
responds to an event it will use the update function returned by the ``use_state`` Hook
to change which image is shown to the user. Calling the update function will schedule
the Component to be re-rendered. That is, the Component's render function will be called
again, and its new result will be displayed.

.. note::

    Even handlers like ``next_image`` which respond to user interactions recieve an
    ``event`` dictionary that contains different information depending on the type of
    event that occured. All supported events and the data they contain are listed
    `here`__.

__ https://reactjs.org/docs/events.html

.. literalinclude:: /examples/slideshow.py
    :lineno-start: 11
    :lines: 11-16
    :linenos:

Finally we come to the end of the ``Slideshow`` body where we return a model for an
``<img/>`` element that draws its image from https://picsum.photos. Our ``next_image``
event handler has been added to the image so that when an ``onClick`` event occurs we
can respond to it. We've also added a little bit of CSS styling to the image so that
when the cursor hoverse over the image it will become a pointer so it appears clickable.
The returned model conforms to the `VDOM mimetype specification`_.

.. literalinclude:: /examples/slideshow.py
    :lineno-start: 20
    :lines: 20
    :linenos:

This last step runs a simple web server that will send the layout of elements defined in
our ``Slideshow`` to the browser and receive any incoming events from the browser via a
websocket. To display the layout we can navigate to http://localhost:8765/client/index.html.

.. note::

    See the :ref:`Examples` section for more info on the ways to display your layouts.


.. Links
.. =====

.. _VDOM event specification: https://github.com/nteract/vdom/blob/master/docs/event-spec.md
.. _VDOM mimetype specification: https://github.com/nteract/vdom/blob/master/docs/mimetype-spec.md
.. _ReactJS: https://reactjs.org/docs/faq-internals.html
.. _React Hooks: https://reactjs.org/docs/hooks-overview.html
