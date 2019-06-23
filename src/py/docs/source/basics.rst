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

The ``idom.element`` decorator indicates that the `asynchronous function`_ to follow
returns a data structure which depcits a user interface, or in more technical terms a
Document Object Model (DOM). We call this structural representation of the DOM a
`Virtual DOM <VDOM React>`_ (VDOM) - a term familiar to those who work with `ReactJS`_.
In the case of ``Slideshow`` it will return a VDOM representing an image which, when
clicked, will change.

.. code:: python

       async def next_image(event):
           self.update(index + 1)

In the lines of code which follow these we will store ``next_image`` as an event
handler that responds when users click our image. Once triggered it will triggered it
will cause us to render the next image in the slideshow. The ``event`` dictionary
which the handler recieves when it is called contains information about the event
occured. All supported events and the data they contain is listed
`here <React events>`__.

.. code-block:: python

        url = f"https://picsum.photos/800/300?image={index}"
        return idom.node("img", src=url, onClick=change_image)

Finally we come the end the ``Slideshow`` body where we return a model for an ``<img/>``
element that draws its image from https://picsum.photos. We've also been sure to add
our ``next_image`` event handler as well so that when an ``onClick`` event occurs we
can respond to it.

.. code-block:: python

    server = idom.server.sanic.PerClientState(Slideshow)
    server.daemon("localhost", 8765).join()

These last steps prepare a simple web server that will send the layout of elements
defined in our ``Slideshow`` to the browser and receive any incoming events from the
browser via a websocket. The server has "per client state" because each client that
connects to it will see a fresh view of the layout. If clients should see views with a
common state you can use the ``SharedClientState`` server instead.

To display the layout we can navigate to http://localhost:8765/client/index.html or
use ``idom.display()`` to show it in a Jupyter Notebook via a widget.

.. Links
.. =====

.. _VDOM event specification: https://github.com/nteract/vdom/blob/master/docs/event-spec.md
.. _VDOM mimetype specification: https://github.com/nteract/vdom/blob/master/docs/mimetype-spec.md
.. _VDOM React: https://reactjs.org/docs/faq-internals.html#what-is-the-virtual-dom
.. _React events: https://reactjs.org/docs/events.html
.. _asynchronous function: https://realpython.com/async-io-python/
.. _ReactJS: https://reactjs.org/docs/faq-internals.html
