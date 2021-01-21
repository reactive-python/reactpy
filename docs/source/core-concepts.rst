Core Concepts
=============

This section covers core features of IDOM that are used in making
interactive interfaces.


Pure Components
---------------

As in most programming paradigms, so many of the problems come down to how we manage
state. The first tool in encouraging its proper curation is the usage of
`pure functions`_. The benefit of a pure function is that there's no state. Similar to
the addage "the best code is no code at all," we make the related claim that "the best
way to manage state is to have no state at all."

With IDOM the core of your application will be built on the back of basic functions and
coroutines that return :ref:`VDOM <VDOM Mimetype>` models and which do so without state
and without `side effects`_. We call these kinds of model rendering functions
:ref:`Pure Components`. For example, one might want a function which
accepted a list of strings and turned it into a series of paragraph elements:

.. code-block::

    def paragraphs(list_of_text):
        return idom.html.div([idom.html.p(text) for text in list_of_text])


Stateful Components
-------------------

A Stateful Component is one which uses a :ref:`Life Cycle Hooks`. These life cycle hooks
allow you to add state to otherwise stateless functions. To create a stateful component
you'll need to apply the :func:`~idom.core.component.component` decorator to a coroutine_
whose body contains a hook usage. We'll demonstrate that with a simple
:ref:`click counter`:

.. testcode::

    import idom


    @idom.component
    def ClickCount():
        count, set_count = idom.hooks.use_state(0)

        return idom.html.button(
            {"onClick": lambda event: set_count(count + 1)},
            [f"Click count: {count}"],
        )


Component Layout
----------------

Displaying components requires you to turn them into :ref:`VDOM <VDOM Mimetype>` -
this is done using a :class:`~idom.core.layout.Layout`. Layouts are responsible for
rendering components (turning them into VDOM) and scheduling their re-renders when they
:meth:`~idom.core.layout.Layout.update`. To create a layout, you'll need a
:class:`~idom.core.component.Component` instance, which will become its root, and won't
ever be removed from the model. Then you'll just need to call and await a
:meth:`~idom.core.layout.Layout.render` which will return a :ref:`JSON Patch`:

.. testcode::

    async with idom.Layout(ClickCount()) as layout:
        patch = await layout.render()

The layout also handles the triggering of event handlers. Normally this is done
automatically by a :ref:`Dispatcher <Layout Dispatcher>`, but for now we'll do it manually.
We can use a trick to hard-code the ``event_handler_id`` so we can pass it, and a fake
event, to the layout's :meth:`~idom.core.layout.Layout.dispatch` method. Then we just
have to re-render the layout and see what changed:

.. testcode::

    from idom.core.layout import LayoutEvent


    event_handler_id = "on-click"


    @idom.component
    def ClickCount():
        count, set_count = idom.hooks.use_state(0)

        @idom.event(target_id=event_handler_id)  # <-- trick to hard code event handler ID
        def on_click(event):
            set_count(count + 1)

        return idom.html.button(
            {"onClick": on_click},
            [f"Click count: {count}"],
        )


    async with idom.Layout(ClickCount()) as layout:
        patch_1 = await layout.render()

        fake_event = LayoutEvent(event_handler_id, [{}])
        await layout.dispatch(fake_event)
        patch_2 = await layout.render()

        for change in patch_2.changes:
            if change["path"] == "/children/0":
                count_did_increment = change["value"] == "Click count: 1"

        assert count_did_increment


Layout Dispatcher
-----------------

An :class:`~idom.core.dispatcher.AbstractDispatcher` implementation is a relatively thin layer
of logic around a :class:`~idom.core.layout.Layout` which drives the triggering of
events and layout updates by scheduling an asynchronous loop that will run forever -
effectively animating the model. To execute the loop, the dispatcher's
:meth:`~idom.core.dispatcher.AbstractDispatcher.run` method accepts two callbacks. One is a
"send" callback to which the dispatcher passes updates, while the other is "receive"
callback that's called by the dispatcher to events it should execute.

.. testcode::

    import asyncio

    from idom.core import SingleViewDispatcher, EventHandler
    from idom.core.layout import LayoutEvent


    sent_patches = []


    async def send(patch):
        sent_patches.append(patch)
        if len(sent_patches) == 5:
            # if we didn't cancel the dispatcher would continue forever
            raise asyncio.CancelledError()


    async def recv():
        event = LayoutEvent(event_handler_id, [{}])

        # We need this so we don't flood the render loop with events.
        # In practice this is never an issue since events won't arrive
        # as quickly as in this example.
        await asyncio.sleep(0)

        return event


    async with SingleViewDispatcher(idom.Layout(ClickCount())) as dispatcher:
        context = None  # see note below
        await dispatcher.run(send, recv, context)

    assert len(sent_patches) == 5


.. note::

    ``context`` is information that's specific to the
    :class:`~idom.core.dispatcher.AbstractDispatcher` implementation. In the case of
    the :class:`~idom.core.dispatcher.SingleViewDispatcher` it doesn't require any
    context. On the other hand the :class:`~idom.core.dispatcher.SharedViewDispatcher`
    requires a client ID as its piece of contextual information.


Layout Server
-------------

The :ref:`Dispatcher <Layout Dispatcher>` allows you to animate the layout, but we still
need to get the models on the screen. One of the last steps in that journey is to send
them over the wire. To do that you need an
:class:`~idom.server.base.AbstractRenderServer` implementation. Presently, IDOM comes
with support for the following web servers:

- :class:`sanic.app.Sanic` (``pip install idom[sanic]``)

  - :class:`idom.server.sanic.PerClientStateServer`

  - :class:`idom.server.sanic.SharedClientStateServer`

- :class:`flask.Flask` (``pip install idom[flask]``)

  - :class:`idom.server.flask.PerClientStateServer`

- :class:`tornado.web.Application` (``pip install idom[tornado]``)

  - :class:`idom.server.tornado.PerClientStateServer`

However, in principle, the base server class is capable of working with any other async
enabled server framework. Potential candidates range from newer frameworks like
`vibora <https://vibora.io/>`__ and `starlette <https://www.starlette.io/>`__ to
`aiohttp <https://aiohttp.readthedocs.io/en/stable/>`__.

.. note::

    If using or implementing a bridge between IDOM and an async server not listed here
    interests you, post an `issue <https://github.com/rmorshea/idom/issues>`__.

The main thing to understand about server implementations is that they can function in
two ways - as a standalone application or as an extension to an existing application.


Standalone Server Usage
.......................

The implementation constructs a default application that's used to serve the dispatched
models:

.. code-block:: python

    import idom
    from idom.server.sanic import PerClientStateServer

    @idom.component
    def View(self):
        return idom.html.h1(["Hello World"])

    app = PerClientStateServer(View)
    app.run("localhost", 5000)


Server Extension Usage
......................

The implementation registers hooks into the application to serve the model once run:

.. code-block:: python

    import idom
    from idom.server.sanic import PerClientState
    from sanic import Sanic

    app = Sanic()

    @idom.component
    def View(self):
        return idom.html.h1(["Hello World"])

    per_client_state = PerClientStateServer(View)
    per_client_state.register(app)

    app.run("localhost", 5000)


.. _pure functions: https://en.wikipedia.org/wiki/Pure_function
.. _side effects: https://en.wikipedia.org/wiki/Side_effect_(computer_science)
.. _coroutine: https://docs.python.org/3/glossary.html#term-coroutine
