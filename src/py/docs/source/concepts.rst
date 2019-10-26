Core Concepts
=============

This section covers core features of IDOM that are used in making
interactive interfaces.

.. contents::
  :local:
  :depth: 1


Pure Elements
-------------

As in most programming paradigms, so many of the problems come down to how
we manage state, and the first tool in encouraging its proper curation is the
usage of `pure functions`_. The benefit of a pure function is that there's no
state, and state that's not there won't be causing bugs.

With IDOM the core of your application will be built on the back of basic
functions and coroutines that return :term:`VDOM` models and which do so without
`side effects`_. We call these kinds of model rendering functions
:term:`Pure Elements <Pure Element>`. There are two ways to create Pure Elements:

1. The most straightforward way is to use a standard function or coroutine

.. code-block::

    def ClickMe():
        return idom.html.button(["Click me!"])

2. But an :func:`idom.element <idom.core.element.element>` decorated coroutine gives you
   the ability to update your element when responding to events. The coroutine's first
   positional argument is an :class:`~idom.core.element.Element` object with an
   :meth:`~idom.core.element.Element.update` method that will schedule the
   coroutine to be re-run with the given arguments.

.. code-block::

    import idom

    @idom.element
    async def ClickCount(self, count):

        async def increment(event):
            self.update(count=count + 1)

        return idom.html.button(
            {"onClick": increment},
            [f"Click count: {count}"],
        )

.. note::

    :func:`idom.element <idom.core.element.element>` turns the decorated function into
    a factory for :class:`~idom.core.element.Element` objects.


Stateful Elements
-----------------

Sometimes, when all else fails, you really do need to keep track of some state. The
simplest way to do this is by adding it to a :ref:`Pure Element <Pure Elements>`
via the :func:`@idom.element <idom.core.element.element>` decorator. By passing the
decorator a string of comma separated parameter names to its ``state`` keyword you can
indicate that those parameters should be retained across updates unless explicitly
changed.

Normally when you call :meth:`Element.update <idom.core.element.Element.update>` you
need to pass it all the arguments that are required by your coroutine. For example, in
the ``ClickCount`` coroutine above we have to explicitly call update with the new
``count``. But if you use the ``state`` keyword, whatever parameter names you specify
there don't need to be explicitly passed because the parameter's last value will be
reused in the next call.

In short this means that instead of writing the following:

.. code-block::

    import idom

    @idom.element
    def ClickHistory(self, event_list):

        async def save_event(event):
            event_list.append(event)
            self.update(event_list=event_list)

        return idom.html.div(
            idom.html.button(["Click me!"]),
            idom.html.p(map(str, event_list)),
        )

You can instead using the ``state`` keyword to make things a little simpler:

.. code-block::
    :emphasize-lines: 3, 8

    import idom

    @idom.element(state="event_list")
    def ClickHistory(self, event_list):

        async def save_event(event):
            event_list.append(event)
            self.update()

        return idom.html.div(
            idom.html.button(["Click me!"]),
            idom.html.p(map(str, event_list)),
        )

.. note::

    Why not just use a default argument ``event_list=[]`` instead? Since default
    arguments are evalauted *once* when the function is defined, they get shared across
    calls. This is one of Python's
    `common pitfalls <https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments>`__.


Class Elements
--------------

If neither :ref:`Pure Elements` or :ref:`Stateful Elements` meet your needs you might
want to define a :term:`Class Element` by creating a subclass of
:class:`~idom.core.element.AbstractElement`. This is most useful if
your element needs an interface which allows you to do more than just
:meth:`~idom.core.element.Element.update` it. You'll find this strategy is used
to implement some of the common IDOM widgets like
:class:`~idom.widgets.inputs.Input` and
:class:`~idom.widgets.images.Image`.

To create a Class Element, you'll need to subclass
:class:`~idom.core.element.AbstractElement`. Doing so is quite straighforward since the
only thing we're required to implement is a
:meth:`~idom.core.element.AbstractElement.render` method. In fact we'll just
quickly reimplement the ``ClickCount`` example from the :ref:`Pure Elements` section:

.. code-block::
    :emphasize-lines: 15

    import idom
    from idom.core import AbstractElement

    class ClickCount(AbstractElement):

        __slots__ = ["_count"]

        def __init__(self):
            super().__init__()
            self._count = 0

        async def render(self):
            async def increment(event):
                self._count += 1
                self._update_layout()

            return idom.html.button(
                {"onClick": increment},
                [f"You clicked {self._count} times"],
            )

.. note::

    ``self._update_layout()`` schedules a re-render of the element -
    this is what :meth:`Element.update <idom.core.element.Element.update>` uses


Element Layout
--------------

Displaying an element requires you to turn elements into :term:`VDOM` - this is done
using a :class:`~idom.core.layout.Layout`. Layouts are responsible for rendering
elements (turning them into VDOM) and scheduling their re-renders when they
:meth:`~idom.core.layout.Layout.update`. To create a layout, you'll need an
:class:`~idom.core.element.Element` instance, which will become its root, and won't
ever be removed from the model. Then you'll just need to call and await a
:meth:`~idom.core.layout.Layout.render` which will return a bundle containing VDOM:

.. code-block::

    import idom
    import json  # just used while printing

    @idom.element
    async def ClickCount(self, count):

        async def increment(event):
            self.update(count=count + 1)

        return idom.html.button(
            {"onClick": increment},
            [f"Click count: {count}"],
        )

    click_count = ClickCounter(0)
    layout = idom.Layout(click_count)
    update = await layout.render()

    print(render.src)  # ID of the element that triggered the update
    print(json.dumps(render.new, indent=2))  # new elements
    print(render.old)  # IDs of elements which were deleted

.. code-block:: text
    :emphasize-lines: 8

    7e44673eb1
    {
      "7e44673eb1": {
        "tagName": "button",
        "children": [
          {
            "type": "str",
            "data": "Click count: 0"
          }
        ],
        "attributes": {},
        "eventHandlers": {
          "onClick": {
            "target": "a42f548630",
            "preventDefault": false,
            "stopPropagation": false
          }
        }
      }
    }
    []

The layout also handles the triggering event handlers. Normally this is done
automatically by a :ref:`Renderer <Layout Renderer>`, but for now we'll do this
manually by digging into the :class:`~idom.core.layout.LayoutUpdate` object to find
the ID of ``click_count``'s event handler so we can execute it. Once we have the ID, we
can pass it, and a fake event, to the layout's :meth:`~idom.core.layout.Layout.trigger`
method. Then we just have to re-render the layout and see what changed:

.. code-block::

    dummy_event = {}
    event_handler_id = update.new[click_count.id]["eventHandlers"]["onClick"]["target"]
    await layout.trigger(event_handler_id, dummy_event)
    new_render = await layout.render()
    print(new_render.new[click_count.id]["children"][0]["data])

.. code-block:: text
    :emphasize-lines: 1

    "Click count: 1"


Layout Renderer
---------------

An :class:`~idom.core.render.AbstractRenderer` implementation is a relatively thin layer
of logic around a :class:`~idom.core.layout.Layout` which drives the triggering of
events and layout updates by scheduling an asynchronous loop that will run forever -
effectively animating the model. To run the loop the renderer's
:meth:`~idom.core.render.AbstractRenderer.run` method accepts two callbacks, one is a
"send" callback to which the renderer passes updates, while the other is "receive"
callback that's called by the renderer to events it should execute.

.. code-block::

    import idom
    from idom.core import SingleStateRenderer, EventHandler
    from idom.core.layout import LayoutEvent
    import asyncio

    event_handler_id = "123456"

    @idom.element
    async def ClickCount(self, count):

        @idom.event(target_id=event_handler_id)  # a trick to hard code the handler ID
        async def increment(event):
            self.update(count=count + 1)

        return idom.html.button(
            {"onClick": increment},
            [f"Click count: {count}"],
        )

    layout = idom.Layout(ClickCount(0))

    async def send_update(update):
        print(update)

    async def recv_event():
        await asyncio.sleep(1)
        fake_event_data = [{}]
        return LayoutEvent(event_handler_id, fake_event_data)

    renderer = SingleStateRenderer(layout)

    context = None  # see note below
    await renderer.run(send_update, recv_event, context)  # this will run forever

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

- :class:`idom.server.sanic.PerClientState`

- :class:`idom.server.sanic.SharedClientState`

The main thing to understand about server implementations is that they can function in
two ways - as a standalone application or as extension to an existing one.


Standalone Server Usage
.......................

The implementation constructs a default application that's used to server the renders of
the model:

.. code-block:: python

    import idom
    from idom.server.sanic import PerClientState

    @idom.element
    def View(self):
        return idom.html.h1(["Hello World"])

    app = PerClientState(View)
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

    per_client_state = PerClientState(View)
    per_client_state.register(app)

    app.run("localhost", 5000)


.. _pure functions: https://en.wikipedia.org/wiki/Pure_function
.. _side effects: https://en.wikipedia.org/wiki/Side_effect_(computer_science)
