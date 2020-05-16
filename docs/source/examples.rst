Examples
========

You can find the following examples and more on binder |launch-binder|:

.. contents::
  :local:
  :depth: 1


Display Function
----------------

Depending on how you plan to use these examples you'll need different
boilerplate code.

In all cases we define a ``display(element)`` function which will display the
view. In a Jupyter Notebook it will appear in an output cell. If you're running
``idom`` as a webserver it will appear at http://localhost:8765/client/index.html.

.. note::

  The :ref:`Shared Client Views` example requires ``SharedClientState`` server instead
  of the ``PerClientState`` server shown in the boilerplate below. Be sure to wwap it
  out when you get there.


**Jupyter Notebook (localhost)**

.. code-block::

    from idom.server import multiview_server
    from idom.server.sanic import PerClientState

    host, port = "127.0.0.1", 8765
    mount, server = multiview_server(PerClientState, host, port, {"cors": True}, {"access_log": False})
    server_url = f"http://{host}:{port}"

    def display(element, *args, **kwargs):
        view_id = mount(element, *args, **kwargs)
        return idom.JupyterDisplay("jupyter", server_url, {"view_id": view_id})


**Jupyter Notebook (binder.org)**

.. code-block::

    import os
    from typing import Mapping, Any, Optional

    from idom.server import multiview_server
    from idom.server.sanic import PerClientState


    def example_server_url(host: str, port: int) -> str:
        localhost_idom_path = f"http://{host}:{port}"
        jupyterhub_idom_path = path_to_jupyterhub_proxy(port)
        return jupyterhub_idom_path or localhost_idom_path


    def path_to_jupyterhub_proxy(port: int) -> Optional[str]:
        """If running on Jupyterhub return the path from the host's root to a proxy server

        This is used when examples are running on mybinder.org or in a container created by
        jupyter-repo2docker. For this to work a ``jupyter_server_proxy`` must have been
        instantiated. See https://github.com/jupyterhub/jupyter-server-proxy
        """
        if "JUPYTERHUB_OAUTH_CALLBACK_URL" in os.environ:
            url = os.environ["JUPYTERHUB_OAUTH_CALLBACK_URL"].rsplit("/", 1)[0]
            return f"{url}/proxy/{port}"
        elif "JUPYTER_SERVER_URL" in os.environ:
            return f"{os.environ['JUPYTER_SERVER_URL']}/proxy/{port}"
        else:
            return None

    host, port = "127.0.0.1", 8765
    mount, server = multiview_server(PerClientState, host, port, {"cors": True}, {"access_log": False})
    server_url = example_server_url(host, port)

    def display(element, *args, **kwargs):
        view_id = mount(element, *args, **kwargs)
        print(f"View ID: {view_id}")
        return idom.JupyterDisplay("jupyter", server_url, {"view_id": view_id})


**Local Python File**

.. code-block::

    from idom.server.sanic import PerClientState

    def display(element, *args, **kwargs):
        PerClientState(element, *args, **kwargs).run("127.0.0.1", 8765)

    # define your element here...

    if __name__ == "__main__":
        display(...)  # pass in the element here


Slideshow
---------

.. code-block::

    @idom.element
    async def Slideshow(self, index=0):

        async def update_image(event):
            self.update(index + 1)

        url = f"https://picsum.photos/800/300?image={index}"
        return idom.html.img({"src": url, "onClick": update_image})

    display(Slideshow)


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

        task_input = idom.html.input({"onKeyDown": add_new_task})
        task_list = TaskList(items)

        return idom.html.div([task_input, task_list])


    @idom.element
    async def TaskList(self, items):
        tasks = []

        for index, text in enumerate(items):

            async def remove(event, index=index):
                del items[index]
                self.update(items)

            task_text = idom.html.td([idom.html.p([text])])
            delete_button = idom.html.td({"onClick": remove}, [idom.html.button(["x"])])
            tasks.append(idom.html.tr([task_text, delete_button]))

        return idom.html.table(tasks)

    display(Todo)


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

        style = idom.html.style(["""
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
        """])

        return idom.html.div([style, h1, h2, h3])


    @idom.element(state="last_owner, last_hover")
    async def Holder(self, kind, last_owner, last_hover):

        @idom.event(prevent_default=True, stop_propagation=True)
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

        return idom.html.div({
            "draggable": (kind == "filled"),
            "onDragStart": start,
            "onDragOver": hover,
            "onDragEnd": end,
            "onDragLeave": leave,
            "onDrop": dropped,
            "class": f"holder-{kind} holder",
        })

    display(DragDropBoxes)


The Game Snake
--------------

.. code-block::

    import enum
    import time
    import random
    import asyncio


    class Directions(enum.Enum):
        ArrowUp = (-1, 0)
        ArrowLeft = (0, -1)
        ArrowDown = (1, 0)
        ArrowRight = (0, 1)


    class GameState:

        def __init__(self, grid_size, block_size):
            self.snake = []
            self.grid = Grid(grid_size, block_size)
            self.new_direction = idom.Var(Directions.ArrowRight)
            self.old_direction = idom.Var(Directions.ArrowRight)
            self.food = idom.Var(None)
            self.won = idom.Var(False)
            self.lost = idom.Var(False)


    @idom.element(state="grid_size, block_size")
    async def GameView(self, grid_size, block_size):
        game = GameState(grid_size, block_size)

        grid_events = game.grid["eventHandlers"]

        @grid_events.on("KeyDown", prevent_default=True)
        async def direction_change(event):
            if hasattr(Directions, event["key"]):
                game.new_direction.set(Directions[event["key"]])

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
            {
                "style": {
                    "height": f"{block_size * grid_size}px",
                    "width": f"{block_size * grid_size}px",
                },

                "tabIndex": -1,
            },
            [
                idom.html.div(
                    {"style": {"height": block_size}},
                    [Block("white", block_size) for i in range(grid_size)]
                )
                for i in range(grid_size)
            ],
            event_handlers=idom.Events(),

        )


    @idom.element(state="block_size")
    async def Block(self, color, block_size):
        return idom.html.div(
            {
                "style": {
                    "height": f"{block_size}px",
                    "width": f"{block_size}px",
                    "backgroundColor": color,
                    "display": "inline-block",
                    "border": "1px solid white",
                }
            }
        )


    def get_grid_block(grid, point):
        x, y = point
        return grid["children"][x]["children"][y]


    display(GameView, 7, 50)


Plotting with Matplotlib
------------------------

.. code-block::

    import time
    import asyncio
    import random

    from matplotlib import pyplot as plt


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

        style = idom.html.style(["""
        .linked-inputs {margin-bottom: 20px}
        .linked-inputs input {width: 48%;float: left}
        .linked-inputs input + input {margin-left: 4%}
        """])

        return idom.html.div({"style": {"width": "60%"}}, [style, plot, mu_inputs, sigma_inputs])


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
        for tp in types:
            inp = idom.Input(tp, value, attributes, cast=float)

            @inp.events.on("change")
            async def on_change(event, inp=inp):
                for i in inputs:
                    i.update(inp.value)
                var.set(inp.value)

            inputs.append(inp)

        fs = idom.html.fieldset({"class": "linked-inputs"}, [idom.html.legend(label)], inputs)

        return var, fs


    print("Try clicking the plot! 📈")

    display(RandomWalk)


Install Javascript Modules
--------------------------

.. code-block::

    victory = idom.Module("victory", install=True)
    VictoryBar = victory.Import("VictoryBar")

    display(VictoryBar, {"style": {"parent": {"width": "500px"}}})


Define Javascript Modules
-------------------------

Assuming you already installed ``victory`` as in the :ref:`Install Javascript Modules` section:

.. code-block::

    with open("chart.js") as f:
        ClickableChart = idom.Module("chart", source=f).Import("ClickableChart")

    async def handle_event(event):
        print(event)

    data = [
        {"x": 1, "y": 2},
        {"x": 2, "y": 4},
        {"x": 3, "y": 7},
        {"x": 4, "y": 3},
        {"x": 5, "y": 5},
    ]

    display(
        ClickableChart,
        {"data": data, "onClick": handle_event, "style": {"parent": {"width": "500px"}}}
    )

Source of ``chart.js``:

.. code-block:: javascript

    import React from "./react.js";
    import { VictoryBar, VictoryChart, VictoryTheme, Bar } from "./victory.js";
    import htm from "./htm.js";

    const html = htm.bind(React.createElement);

    export default {
      ClickableChart: function ClickableChart(props) {
        return html`
          <${VictoryChart}
            theme=${VictoryTheme.material}
            style=${props.style}
            domainPadding=${20}
          >
            <${VictoryBar}
              data=${props.data}
              dataComponent=${html`
                <${Bar}
                  events=${{
                    onClick: props.onClick,
                  }}
                />
              `}
            />
          <//>
        `;
      },
    };


Shared Client Views
-------------------

This example requires the :ref:`idom.server.sanic.SharedClientState` server. Be sure to
replace it in your boilerplate code before going further! Once you've done this we can
just re-display our :ref:`Slideshow` example using the new server. Now all we need to do
is connect to the server with a couple clients to see that their views are synced. This
can be done by navigating to the server URL in seperate browser tabs. Likewise if you're
using a Jupyter Notebook you would display it in multiple cells like this:

**Jupyter Notebook**

.. code-block::

    # Cell 1
    ...  # boiler plate with SharedClientState server

    # Cell 2
    ...  # code from the Slideshow example

    # Cell 3
    widget = display(Slideshow)

    # Cell 4
    widget  # this is our first view

    # Cell 5
    widget  # this is out second view


.. Links
.. =====

.. |launch-binder| image:: https://mybinder.org/badge_logo.svg
 :target: https://mybinder.org/v2/gh/rmorshea/idom/master?filepath=examples%2Fintroduction.ipynb
