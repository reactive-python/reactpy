Getting Started
===============

Let's reexamine the example that you may have seen :ref:`at a glance <At a Glance>` on the
homepage:

.. code:: python

    import idom

    @idom.element
    async def Slideshow(self, index=0):

        async def next_image(event):
            self.update(index + 1)

        url = f"https://picsum.photos/800/300?image={index}"
        return idom.node("img", src=url, onClick=next_image)

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

       async def next_image(event):
           self.update(index + 1)

In the next few lines of code this ``next_image`` coroutine will get
stored as an event handler that responds when users click our image.
Once triggered it will triggered it will cause us to re-render the
next image in the slideshow. The ``event`` dictionary which the handler
recieves when it is called contains information about the event occured.
All supported events and the data they contain is listed `here <React events>`__.

.. code-block:: python

        url = f"https://picsum.photos/800/300?image={index}"
        return idom.node("img", src=url, onClick=change_image)

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
