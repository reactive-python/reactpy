import enum
import time
import random
import asyncio

import idom

from _utils import click_to_start


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


@click_to_start
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
                [Block("white", block_size) for i in range(grid_size)],
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
                "box-sizing": "border-box",
            }
        }
    )


def get_grid_block(grid, point):
    x, y = point
    return grid["children"][x]["children"][y]


display(GameView, 7, 50)
