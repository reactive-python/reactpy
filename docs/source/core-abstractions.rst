Core Abstractions
=================


Pure Components
---------------

As in most programming paradigms, so many of the problems come down to how we manage
state. The first tool in encouraging its proper curation is the usage of
`pure functions`_. The benefit of a pure function is that there's no state. Similar to
the adage "the best code is no code at all," we make the related claim that "the best
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


    def use_counter():
        count, set_count = idom.hooks.use_state(0)
        return count, lambda: set_count(lambda old_count: old_count + 1)


    @idom.component
    def ClickCount():
        count, increment_count = use_counter()
        return idom.html.button(
            {"onClick": lambda event: increment_count()},
            [f"Click count: {count}"],
        )


Component Layout
----------------

Displaying components requires you to turn them into :ref:`VDOM <VDOM Mimetype>`. This
transformation, known as "rendering a component", is done by a
:class:`~idom.core.proto.LayoutType`. Layouts are responsible for rendering components
and scheduling their re-renders when they change. IDOM's concrete
:class:`~idom.core.layout.Layout` implementation renders
:class:`~idom.core.component.Component` instances into
:class:`~idom.core.layout.LayoutUpdate` and responds to
:class:`~idom.core.layout.LayoutEvent` objects respectively.

To create a layout, you'll need a :class:`~idom.core.component.Component` instance, that
will become its root. This component won't ever be removed from the model. Then, you'll
just need to call and await a :meth:`~idom.core.layout.Layout.render` which will return
a :ref:`JSON Patch`:


.. testcode::

    with idom.Layout(ClickCount()) as layout:
        update = await layout.render()

The layout also handles the deliver of events to their handlers. Normally these are sent
through a :ref:`Dispatcher <Layout Dispatcher>` first, but for now we'll do it manually.
To accomplish this we need to pass a fake event with its "target" (event handler
identifier), to the layout's :meth:`~idom.core.layout.Layout.deliver` method, after
which we can re-render and see what changed:

.. testcode::

    from idom.core.layout import LayoutEvent
    from idom.testing import StaticEventHandler

    static_handler = StaticEventHandler()


    @idom.component
    def ClickCount():
        count, increment_count = use_counter()

        # we do this in order to capture the event handler's target ID
        handler = static_handler.use(lambda event: increment_count())

        return idom.html.button({"onClick": handler}, [f"Click count: {count}"])


    with idom.Layout(ClickCount()) as layout:
        update_1 = await layout.render()

        fake_event = LayoutEvent(target=static_handler.target, data=[{}])
        await layout.deliver(fake_event)

        update_2 = await layout.render()
        assert update_2.new["children"][0] == "Click count: 1"

.. note::

    Don't worry about the format of the layout event's ``target``. Its an internal
    detail of the layout's implementation that is neither necessary to understanding
    how things work, nor is it part of the interface clients should rely on.


Layout Dispatcher
-----------------

A "dispatcher" implementation is a relatively thin layer of logic around a
:class:`~idom.core.layout.Layout` which drives the triggering of events and updates by
scheduling an asynchronous loop that will run forever - effectively animating the model.
The simplest dispatcher is :func:`~idom.core.dispatcher.dispatch_single_view` which
accepts three arguments. The first is a :class:`~idom.core.layout.Layout`, the second is
a "send" callback to which the dispatcher passes updates, and the third is a "receive"
callback that's called by the dispatcher to collect events it should execute.

.. testcode::

    import asyncio

    from idom.core.layout import LayoutEvent
    from idom.core.dispatcher import dispatch_single_view


    sent_patches = []

    # We need this to simulate a scenario in which events arriving *after* each update
    # has been sent to the client. Otherwise the events would all arrive at once and we
    # would observe one large update rather than many discrete updates.
    semaphore = asyncio.Semaphore(0)


    async def send(patch):
        sent_patches.append(patch)
        semaphore.release()
        if len(sent_patches) == 5:
            # if we didn't cancel the dispatcher would continue forever
            raise asyncio.CancelledError()


    async def recv():
        await semaphore.acquire()
        event = LayoutEvent(target=static_handler.target, data=[{}])
        return event


    await dispatch_single_view(idom.Layout(ClickCount()), send, recv)
    assert len(sent_patches) == 5


.. note::

    The :func:`~idom.core.dispatcher.create_shared_view_dispatcher`, while more complex
    in its usage, allows multiple clients to share one synchronized view.


Layout Server
-------------

The :ref:`Dispatcher <Layout Dispatcher>` allows you to animate the layout, but we still
need to get the models on the screen. One of the last steps in that journey is to send
them over the wire. To do that you need a :class:`~idom.server.proto.ServerFactory`
implementation. Presently, IDOM comes with support for the following web servers:

- :class:`sanic.app.Sanic` (``pip install idom[sanic]``)

  - :class:`idom.server.sanic.PerClientStateServer`

  - :class:`idom.server.sanic.SharedClientStateServer`

- `fastapi.FastAPI <https://fastapi.tiangolo.com/>`__ (``pip install idom[fastapi]``)

  - :class:`idom.server.fastapi.PerClientStateServer`

  - :class:`idom.server.fastapi.SharedClientStateServer`

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

    per_client_state = PerClientStateServer(View, app=app)

    app.run("localhost", 5000)


.. _pure functions: https://en.wikipedia.org/wiki/Pure_function
.. _side effects: https://en.wikipedia.org/wiki/Side_effect_(computer_science)
.. _coroutine: https://docs.python.org/3/glossary.html#term-coroutine
