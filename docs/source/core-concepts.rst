Core Concepts
=============

This section covers core features of IDOM that are used in making
interactive interfaces.

.. contents::
  :local:
  :depth: 1


Pure Elements
-------------

As in most programming paradigms, so many of the problems come down to how we manage
state, and the first tool in encouraging its proper curation is the usage of
`pure functions`_. The benefit of a pure function is that there's no state. Similar to
the addage "the best code is no code at all," we make the related claim that "the best
way to manage state is to have no state at all."

With IDOM the core of your application will be built on the back of basic functions and
coroutines that return :term:`VDOM` models and which do so without state and without
`side effects`_. We call these kinds of model rendering functions
:term:`Pure Elements <Pure Element>`. For example, one might want a function which
accepted a list of strings and turned it into a series of paragraph elements:

.. code-block::

    def paragraphs(list_of_text):
        return idom.html.div([idom.html.p(text) for text in list_of_text])


Stateful Elements
-----------------

A Stateful Element is one which uses a :ref:`Life Cycle Hook`. These lifecycle hooks
allow you to add state to otherwise stateless functions. To create a stateful element
you'll need to apply the :func:`~idom.core.element.element` decorator to a coroutine_
whose body contains a hook usage. We'll demonstrate that with a simple
:ref:`click counter`:

.. testcode::

    import idom


    @idom.element
    async def ClickCount():
        count, set_count = idom.hooks.use_state(0)

        return idom.html.button(
            {"onClick": lambda event: set_count(count + 1)},
            [f"Click count: {count}"],
        )


Element Layout
--------------

Displaying an element requires you to turn elements into :term:`VDOM` - this is done
using a :class:`~idom.core.layout.Layout`. Layouts are responsible for rendering
elements (turning them into VDOM) and scheduling their re-renders when they
:meth:`~idom.core.layout.Layout.update`. To create a layout, you'll need an
:class:`~idom.core.element.Element` instance, which will become its root, and won't
ever be removed from the model. Then you'll just need to call and await a
:meth:`~idom.core.layout.Layout.render` which will return a :ref:`JSON Patch`:

.. testcode::

    async with idom.Layout(ClickCount()) as layout:
        patch = await layout.render()

The layout also handles the triggering event handlers. Normally this is done
automatically by a :ref:`Renderer <Layout Renderer>`, but for now we'll to it manually.
To do use we can use a trick to hard-code the ``event_handler_id`` so we can pass it,
and a fake event, to the layout's :meth:`~idom.core.layout.Layout.dispatch` method. Then
we just have to re-render the layout and see what changed:

.. testcode::

    from idom.core.layout import LayoutEvent


    event_handler_id = "on-click"


    @idom.element
    async def ClickCount():
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


Layout Renderer
---------------

An :class:`~idom.core.render.AbstractRenderer` implementation is a relatively thin layer
of logic around a :class:`~idom.core.layout.Layout` which drives the triggering of
events and layout updates by scheduling an asynchronous loop that will run forever -
effectively animating the model. To run the loop the renderer's
:meth:`~idom.core.render.AbstractRenderer.run` method accepts two callbacks, one is a
"send" callback to which the renderer passes updates, while the other is "receive"
callback that's called by the renderer to events it should execute.

.. testcode::

    import asyncio

    from idom.core import SingleStateRenderer, EventHandler
    from idom.core.layout import LayoutEvent


    sent_patches = []


    async def send(patch):
        sent_patches.append(patch)
        if len(sent_patches) == 5:
            # if we didn't cancel the renderer would continue forever
            raise asyncio.CancelledError()


    async def recv():
        event = LayoutEvent(event_handler_id, [{}])

        # We need this so we don't flood the render loop with events.
        # In practice this is never an issue since events won't arrive
        # as quickly as in this example.
        await asyncio.sleep(0)

        return event


    async with SingleStateRenderer(idom.Layout(ClickCount())) as renderer:
        context = None  # see note below
        await renderer.run(send, recv, context)

    assert len(sent_patches) == 5


.. note::

    ``context`` is information that's specific to the
    :class:`~idom.core.render.AbstractRenderer` implementation. In the case of
    the :class:`~idom.core.render.SingleStateRenderer` it doesn't require any
    context. On the other hand the :class:`~idom.core.render.SharedStateRenderer`
    requires a client ID as its piece of contextual information.


Layout Server
-------------

The :ref:`Renderer <Layout Renderer>` allows you to animate the layout, but we still
need to get the models on the screen, and one of the last steps in that journey is to
send them over the wire. To do that you need an
:class:`~idom.server.base.AbstractRenderServer` implementation. Right now we have a
builtin subclass that relies on :mod:`sanic`, an async enabled web server. In principle
though, the base server class is capable of working with any other async enabled server
framework. Potential candidates range from newer frameworks like
`vibora <https://vibora.io/>`__, `starlette <https://www.starlette.io/>`__, and
`aiohttp <https://aiohttp.readthedocs.io/en/stable/>`__ to older ones that are
starting to add support for asyncio like
`tornado <https://www.tornadoweb.org/en/stable/asyncio.html>`__.

.. note::
    If using or implementing a bridge between IDOM and these servers interests you post
    an `issue <https://github.com/rmorshea/idom/issues>`__.

In the case of our :class:`~idom.server.sanic.SanicRenderServer` types we have one
implementation per builtin :ref:`Renderer <Layout Renderer>`:

- :class:`idom.server.sanic.PerClientStateServer`

- :class:`idom.server.sanic.SharedClientStateServer`

The main thing to understand about server implementations is that they can function in
two ways - as a standalone application or as an extension to an existing application.


Standalone Server Usage
.......................

The implementation constructs a default application that's used to server the renders of
the model:

.. code-block:: python

    import idom
    from idom.server.sanic import PerClientStateServer

    @idom.element
    def View(self):
        return idom.html.h1(["Hello World"])

    app = PerClientStateServer(View)
    app.run("localhost", 5000)


Server Extension Usage
......................

The implementation registers hooks into the application to server the model once run:

.. code-block:: python

    import idom
    from idom.server.sanic import PerClientState
    from sanic import Sanic

    app = Sanic()

    @idom.element
    def View(self):
        return idom.html.h1(["Hello World"])

    per_client_state = PerClientStateServer(View)
    per_client_state.register(app)

    app.run("localhost", 5000)


.. _pure functions: https://en.wikipedia.org/wiki/Pure_function
.. _side effects: https://en.wikipedia.org/wiki/Side_effect_(computer_science)
.. _coroutine: https://docs.python.org/3/glossary.html#term-coroutine
