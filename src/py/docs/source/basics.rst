Getting Started
===============

Let's reexamine the example that you may have seen :ref:`at a glance <At a Glance>` on the
homepage:

.. code:: python

    import idom

    @idom.element
    async def Slideshow(self, index=0):
        events = idom.Events()

        @events.on("click")
        async def change():
            self.update(index + 1)

        url = f"https://picsum.photos/800/300?image={index}"
        return idom.node("img", src=url, eventHandlers=events)

    server = idom.server.sanic.PerClientState(Slideshow)
    server.daemon("localhost", 8765).join()

Since this may have been a lot to take in at once we'll break it down piece by piece:

.. code:: python

   @idom.element
   async def Slideshow(self, index=0):

The ``idom.element`` decorator indicates that the `asynchronous
function`_ to follow returns a data structure which represents a user
interface or Document Object Model (DOM). We call this structural
representation of the DOM a [Virtual DOM] (VDOM) - a term familiar to
those who work with `ReactJS`_. In the case of ``Slideshow`` it will
return a VDOM representing an image which, when clicked, will change.

.. code:: python

       events = idom.Events()

``Events`` creates an object to which event handlers will be assigned.
Adding an ``Events`` object to a VDOM will given you the ability to
respond when users interact with you interface. Under the hood though,
``Events`` is just a mapping that conforms to the `VDOM event
specification`_.

.. code:: python

       @events.on("click")
       async def change():
           self.update(index + 1)

By using the ``idom.Events()`` object we created above, we can register
a function as an event handler. This handler will be called once a user
clicks on the image. All supported events are listed `here <React events>`_.

You can add parameters to this handler which will allow you to access
attributes of the JavaScript event which occurred in the browser. For
example when a key is pressed in an ``<input/>`` element you can access
the key’s name by adding a ``key`` parameter to the event handler.

Inside the handler itself we update ``self`` which is out ``Slideshow``
element. Calling ``self.update(*args, **kwargs)`` will schedule a new
render of the ``Slideshow`` element to be performed with new parameters.

.. code-block:: python

        url = f"https://picsum.photos/800/300?image={index}"
        return idom.node("img", src=url, eventHandlers=events)

We return a model for an ``<img/>`` element which draws its image from https://picsum.photos
and will respond to the ``events`` we defined earlier. Similarly to the ``events`` object
``idom.node`` returns a mapping which conforms to the `VDOM mimetype specification`_.

.. code-block:: python

    server = idom.server.sanic.PerClientState(Slideshow)
    server.daemon("localhost", 8765).join()

This sets up a simple web server which will display the layout of elements and update
them when events occur over a websocket. The server has "per client state" because
each client that connects to it will see a fresh view of the layout. If clients should
see views with a common state you can use the ``SharedClientState`` server.

To display the layout we can navigate to http://localhost:8765/client/index.html or
use ``idom.display()`` to show it in a Jupyter Notebook via a widget.

.. Links
.. =====

.. _VDOM event specification: https://github.com/nteract/vdom/blob/master/docs/event-spec.md
.. _VDOM mimetype specification: https://github.com/nteract/vdom/blob/master/docs/mimetype-spec.md
.. _React events: https://reactjs.org/docs/events.html
.. _asynchronous function: https://realpython.com/async-io-python/
.. _ReactJS: https://reactjs.org/docs/faq-internals.html
