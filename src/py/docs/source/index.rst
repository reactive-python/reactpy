iDOM
====

Libraries for defining and controlling interactive webpages with Python
3.6 and above.

.. toctree::
    :maxdepth: 1

    install
    api
    glossary


Early Days
----------

iDOM is still young. If you have ideas or find a bug, be sure to post an
`issue`_ or create a `pull request`_. Thanks in advance!


At a Glance
-----------

Let's use iDOM to create a simple slideshow which changes whenever a
user clicks an image:

.. code:: python

   import idom

   @idom.element
   async def slideshow(self, index=0):
       events = idom.Events()

       @events.on("click")
       def change():
           self.update(index + 1)

       url = f"https://picsum.photos/800/300?image={index}"
       return idom.node("img", src=url, eventHandlers=events)

   idom.SimpleWebServer(slideshow).daemon("localhost", 8765).join()

Running this will serve our slideshow to
``"https://localhost:8765/idom/client/index.html"``

.. image:: https://picsum.photos/700/300?random

You could even display the same thing in a Jupyter notebook!

.. code:: python

   idom.display("jupyter", "https://localhost:8765/idom/stream")

Every click will then cause the image to change (it won’t here of
course).


Breaking it Down
----------------

That might have been a bit much to throw out at once. Let’s break down
each piece of the example above:

.. code:: python

   @idom.element
   async def slideshow(self, index=0):

The decorator indicates that the function or coroutine to follow defines
an update-able element. The ``slideshow`` coroutine is responsible for
building a DOM model, and every time an update is triggered, it will be
called with new parameters to recreate the model.

.. code:: python

       events = idom.Events()

Creates an object to which event handlers will be assigned. Adding
``events`` to a DOM model will given you the ability to respond to
events that may be triggered when users interact with the image. Under
the hood though, ``events`` is just a mapping which conforms to the
`VDOM event specification`_.

.. code:: python

       @events.on("click")
       def change():
           self.update(index + 1)

By using the ``idom.Events()`` object we created above, we can register
a function as an event handler. This handler will be called once a user
clicks on the image. All supported events are listed `here <React events>`_.

You can add parameters to this handler which will allow you to access
attributes of the JavaScript event which occurred in the browser. For
example when a key is pressed in an ``<input/>`` element you can access
the key’s name by adding a ``key`` parameter to the event handler.

Inside the handler itself we update ``self`` which is out ``slideshow``
element. Calling ``self.update(*args, **kwargs)`` will schedule a new
render of the ``slideshow`` element to be performed with new \`

.. Links
.. =====

.. _issue: https://github.com/rmorshea/idom/issues
.. _pull request: https://github.com/rmorshea/idom/pulls
.. _VDOM event specification: https://github.com/nteract/vdom/blob/master/docs/event-spec.md
.. _React events: https://reactjs.org/docs/events.html
