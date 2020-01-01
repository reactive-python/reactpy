Examples
========

You can find the following examples on binder |launch-binder|:

.. contents::
  :local:
  :depth: 1

Depending on how you plan to use these examples you'll need different
boilerplate code.

In all cases we define a ``show(element)`` function which will display the
view. In a Jupyter Notebook it will appear in an output cell. If you're running
``idom`` as a webserver it will appear at http://localhost:8765/client/index.html.

.. note::

  The :ref:`Shared Client Views` example requires ``SharedClientState`` server instead
  of the ``PerClientState`` server shown in the boilerplate below. Be sure to wwap it
  out when you get there.


**Jupyter Notebook (localhost)**

.. code-block::

    import idom
    mount, root = idom.hotswap()
    idom.server.sanic.PerClientState(root).daemon("localhost", 8765, access_log=False)

    def show(element=None, *args, **kwargs):
        if element is not None:
            mount(element, *args, **kwargs)
        # make this the output of your cell
        return idom.display("jupyter", "ws://127.0.0.1:8765/stream")


**Jupyter Notebook (binder.org)**

.. code-block::

    import idom
    mount, root = idom.hotswap()
    idom.server.sanic.PerClientState(root).daemon("localhost", 8765, access_log=False)

    def proxy_uri_root(protocol, port):
        if "JUPYTERHUB_OAUTH_CALLBACK_URL" in os.environ:
            auth = os.environ["JUPYTERHUB_OAUTH_CALLBACK_URL"].rsplit("/", 1)[0]
            return "%s/proxy/%s" % (auth, port)
        elif "JUPYTER_SERVER_URL" in os.environ:
            return "%s/proxy/%s" % (os.environ["JUPYTER_SERVER_URL"], port)
        else:
            raise RuntimeError("Unknown JupyterHub environment.")

    def show(element=None, *args, **kwargs):
        if element is not None:
            mount(element, *args, **kwargs)
        # make this the output of your cell
        websocket_url = proxy_uri_root("ws", 8765) + "/stream"
        return idom.display("jupyter", websocket_url)


**Local Python File**

.. code-block::

    import idom

    def show(element, *args, **kwargs):
        # this is a blocking call so run this in `if __name__ == "__main__":`
        PerClientState(element, *args, **kwargs).run("localhost", 8765)


To Do List
----------

.. code-block::

    @idom.element
    async def Todo(self):
        items = []

        async def add_new_task(event):
            if event["key"] == "Enter":
                items.append(event["value"])
                task_list.update(items)

        task_input = idom.html.input(onKeyDown=add_new_task)
        task_list = TaskList(items)

        return idom.html.div(task_input, task_list)


    @idom.element
    async def TaskList(self, items):
        tasks = []

        for index, text in enumerate(items):

            async def remove(event, index=index):
                del items[index]
                self.update(items)

            task_text = idom.html.td(idom.html.p(text))
            delete_button = idom.html.td(idom.html.button("x"), onClick=remove)
            tasks.append(idom.html.tr(task_text, delete_button))

        return idom.vdom("table", tasks)

    show(Todo)


Drag and Drop
-------------

.. code-block::

    @idom.element
    async def DragDropBoxes(self):
        last_owner =idom.Var(None)
        last_hover = idom.Var(None)

        h1 = Holder("filled", last_owner, last_hover)
        h2 = Holder("empty", last_owner, last_hover)
        h3 = Holder("empty", last_owner, last_hover)

        last_owner.set(h1)

        style = idom.html.style("""
        .holder {
          height: 150px;
          width: 150px;
          margin: 20px;
          display: inline-block;
        }
        .holder-filled {
          border: solid 10px black;
          background-color: black;
        }
        .holder-hover {
          border: dotted 5px black;
        }
        .holder-empty {
          border: solid 5px black;
          background-color: white;
        }
        """)

        return idom.html.div(style, h1, h2, h3)


    @idom.element(state="last_owner, last_hover")
    async def Holder(self, kind, last_owner, last_hover):

        @idom.event(preventDefault=True, stopPropagation=True)
        async def hover(event):
            if kind != "hover":
                self.update("hover")
                old = last_hover.set(self)
                if old is not None and old is not self:
                    old.update("empty")

        async def start(event):
            last_hover.set(self)
            self.update("hover")

        async def end(event):
            last_owner.get().update("filled")

        async def leave(event):
            self.update("empty")

        async def dropped(event):
            if last_owner.get() is not self:
                old = last_owner.set(self)
                old.update("empty")
            self.update("filled")

        return idom.html.div(
            draggable=(kind == "filled"),
            onDragStart=start,
            onDragOver=hover,
            onDragEnd=end,
            onDragLeave=leave,
            onDrop=dropped,
            cls=f"holder-{kind} holder",
        )

    show(DragDropBoxes)


The Game Snake
--------------

.. code-block::

    import enum
    import time
    import random
    import asyncio


    class WASD(enum.Enum):
        w = (-1, 0)
        a = (0, -1)
        s = (1, 0)
        d = (0, 1)


    class GameState:

        def __init__(self, grid_size, block_size):
            self.snake = []
            self.grid = Grid(grid_size, block_size)
            self.new_direction = idom.Var(WASD.d)
            self.old_direction = idom.Var(WASD.d)
            self.food = idom.Var(None)
            self.won = idom.Var(False)
            self.lost = idom.Var(False)


    @idom.element(state="grid_size, block_size")
    async def GameView(self, grid_size, block_size):
        game = GameState(grid_size, block_size)

        grid_events = game.grid["eventHandlers"]

        @grid_events.on("KeyDown")
        async def direction_change(event):
            if hasattr(WASD, event["key"]):
                game.new_direction.set(WASD[event["key"]])

        game.snake.extend(
            [
                (grid_size // 2 - 1, grid_size // 2 - 3),
                (grid_size // 2 - 1, grid_size // 2 - 2),
                (grid_size // 2 - 1, grid_size // 2 - 1),
            ]
        )

        grid_points = set((x, y) for x in range(grid_size) for y in range(grid_size))

        def set_new_food():
            points_not_in_snake = grid_points.difference(game.snake)
            new_food = random.choice(list(points_not_in_snake))
            get_grid_block(game.grid, new_food).update("blue")
            game.food.set(new_food)

        @self.animate(rate=0.5)
        async def loop(stop):
            if game.won.get() or game.lost.get():
                await asyncio.sleep(1)
                self.update()
            else:
                await draw(game, grid_size, set_new_food)

        set_new_food()
        return game.grid


    async def draw(game, grid_size, set_new_food):
        if game.snake[-1] in game.snake[:-1]:
            # point out where you touched
            get_grid_block(game.grid, game.snake[-1]).update("red")
            game.lost.set(True)
            return

        vector_sum = tuple(
            map(sum, zip(game.old_direction.get().value, game.new_direction.get().value))
        )
        if vector_sum != (0, 0):
            game.old_direction.set(game.new_direction.get())

        new_head = (
            # grid wraps due to mod op here
            (game.snake[-1][0] + game.old_direction.get().value[0]) % grid_size,
            (game.snake[-1][1] + game.old_direction.get().value[1]) % grid_size,
        )

        game.snake.append(new_head)

        if new_head == game.food.get():
            if len(game.snake) == grid_size * grid_size:
                get_grid_block(game.grid, new_head).update("yellow")
                game.won.set(True)
                return
            set_new_food()
        else:
            get_grid_block(game.grid, game.snake.pop(0)).update("white")

        # update head after tail - new head may be the same as the old tail
        get_grid_block(game.grid, new_head).update("black")


    def Grid(grid_size, block_size):
        return idom.html.div(
            [
                idom.html.div(
                    [Block("white", block_size) for i in range(grid_size)],
                    style={"height": block_size},
                )
                for i in range(grid_size)
            ],
            style={
                "height": f"{block_size * grid_size}px",
                "width": f"{block_size * grid_size}px",
            },
            eventHandlers=idom.Events(),
            tabIndex=-1,
        )


    @idom.element(state="block_size")
    async def Block(self, color, block_size):
        return idom.html.div(
            style={
                "height": f"{block_size}px",
                "width": f"{block_size}px",
                "backgroundColor": color,
                "display": "inline-block",
                "border": "1px solid white",
            }
        )


    def get_grid_block(grid, point):
        x, y = point
        return grid["children"][x]["children"][y]

    show(GameView)


Plotting with Matplotlib
------------------------

.. code-block::

    import time
    import asyncio
    import random


    @idom.element
    async def RandomWalk(self):
        x, y = [0] * 50, [0] * 50
        plot = Plot(x, y)

        mu_var, mu_inputs = linked_inputs(
            "Mean", 0, "number", "range", min=-1, max=1, step=0.01
        )
        sigma_var, sigma_inputs = linked_inputs(
            "Standard Deviation", 1, "number", "range", min=0, max=2, step=0.01
        )

        @self.animate(rate=0.3)
        async def walk(stop):
            x.pop(0)
            x.append(x[-1] + 1)
            y.pop(0)
            diff = random.gauss(float(mu_var.get()), float(sigma_var.get()))
            y.append(y[-1] + diff)
            plot.update(x, y)

        style = idom.html.style("""
        .linked-inputs {margin-bottom: 20px}
        .linked-inputs input {width: 48%;float: left}
        .linked-inputs input + input {margin-left: 4%}
        """)

        return idom.html.div(style, plot, mu_inputs, sigma_inputs, style={"width": "60%"})


    @idom.element(run_in_executor=True)
    async def Plot(self, x, y):
        fig, axes = plt.subplots()
        axes.plot(x, y)
        img = idom.Image("svg")
        fig.savefig(img.io, format="svg")
        plt.close(fig)
        return img


    def linked_inputs(label, value, *types, **attributes):
        var = idom.Var(value)

        inputs = []
        for t in types:
            inp = idom.Input(t, value, **attributes)

            @inp.events.on("change")
            async def on_change(inp, event):
                for i in inputs:
                    i.update(inp.value)
                var.set(inp.value)

            inputs.append(inp)

        fs = idom.html.fieldset(idom.html.legend(label), *inputs, cls="linked-inputs")

        return var, fs


Import Javascript
-----------------

.. code-block::

    antd = idom.Import("https://dev.jspm.io/antd")

    @idom.element
    async def AntDatePicker(self):

        async def changed(moment, datestring):
            print("CLIENT DATETIME:", moment)
            print("PICKED DATETIME:", datestring)

        return idom.html.div(
            idom.html.link(rel="stylesheet", type="text/css", href="https://dev.jspm.io/antd/dist/antd.css"),
            antd.DatePicker(onChange=changed, fallback="Loading...")
        )


Shared Client Views
-------------------

This example requires the ``SharedClientState`` server. Be sure to replace it in your
boilerplate code before going further! Once you've done this we can just re-display our
:ref:`Drag and Drop` example using the new server. No all we need to do is connect to
the server with a couple clients to see that their views are synced.

However, connecting to the server will be different depending on your environment:

**Jupyter Notebook**

.. code-block::

    # Cell 1
    ...  # boiler plate with SharedClientState server

    # Cell 2
    ...  # code from the Drag and Drop example

    # Cell 3
    display = show(DragAndDrop)

    # Cell 4
    display  # this is our first view

    # Cell 5
    display  # this is out second view


**Local Python File**

Replace the ``SharedClientState`` in your boilerplate, copy the :ref:`Drag and Drop`
example code and run it. Now all you need to do is open up
http://localhost:8765/client/index.html in two different windows and view
them side-by-side.


.. Links
.. =====

.. |launch-binder| image:: https://mybinder.org/badge_logo.svg
 :target: https://mybinder.org/v2/gh/rmorshea/idom/master?filepath=examples%2Fintroduction.ipynb
