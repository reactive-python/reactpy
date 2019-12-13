Getting Started
===============

Let's look at the example that you may have seen
:ref:`at a glance <At a Glance>` on the homepage:

.. code-block::

    import idom

    @idom.element
    async def Slideshow(self, index=0):

        async def next_image(event):
            self.update(index + 1)

        url = f"https://picsum.photos/800/300?image={index}"
        return idom.html.img({"src": url, "onChange": next_image})

    server = idom.server.sanic.PerClientState(Slideshow)
    server.daemon("localhost", 8765).join()

Since it's likely a lot to take in at once we'll break it down piece by piece:

.. code-block::

   @idom.element
   async def Slideshow(self, index=0):

The ``idom.element`` decorator indicates that the `asynchronous function`_ to follow
returns a data structure which depicts a user interface, or in more technical terms a
Document Object Model (DOM). We call this structural representation of the DOM a
`Virtual DOM`__ (VDOM) - a term familiar to those who work with `ReactJS`_.
In the case of ``Slideshow`` it will return a VDOM representing an image which, when
clicked, will change.

__ https://reactjs.org/docs/faq-internals.html#what-is-the-virtual-dom

A key thing to note here though is the use of ``self`` as a parameter to ``Slideshow``.
Similarly to how ``self`` refers to the current instance of class when used as a
parameter of its methods, ``self`` in the context of an
:func:`idom.element <idom.core.element.element>`
decorated coroutines refers to the current :class:`Element <idom.core.element.Element>`
instance.

.. code-block::

       async def next_image(event):
           self.update(index + 1)

The coroutine above uses the reference to the current element instance in ``self`` to
:meth:`update() <idom.core.element.Element.update>` to our view of the slideshow. The
effect of calling this update method is to schedule a re-render of of our ``Slideshow``
using the newly incremented index.

.. note::

    Coroutines like ``next_image`` which respond to user interactions recieve an
    ``event`` dictionary that contains different information depending on they type
    of event that occured. All supported events and the data they contain is listed
    `here`__.

__ https://reactjs.org/docs/events.html

.. code-block::

        url = f"https://picsum.photos/800/300?image={index}"
        return idom.html.img({"src": url, "onChange": next_image})

Finally we come the end the ``Slideshow`` body where we return a model for an ``<img/>``
element that draws its image from https://picsum.photos. We've also been sure to add
our ``next_image`` event handler as well so that when an ``onClick`` event occurs we
can respond to it. The returned model conforms to the `VDOM mimetype specification`_.

.. code-block::

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
.. _asynchronous function: https://realpython.com/async-io-python/
.. _ReactJS: https://reactjs.org/docs/faq-internals.html
