import enum
import time
import random
import asyncio

import idom


class Direction(enum.Enum):
    ArrowUp = (-1, 0)
    ArrowLeft = (0, -1)
    ArrowDown = (1, 0)
    ArrowRight = (0, 1)


@idom.element
async def GameView(grid_size, block_size):
    await idom.hooks.use_interval(2)

    grid_events = idom.Events()

    direction, set_direction = idom.hooks.use_state(Direction.ArrowRight)

    @grid_events.on("KeyDown", prevent_default=True)
    async def on_direction_change(event):
        if hasattr(Direction, event["key"]):
            maybe_new_direction = Direction[event["key"]]
            direction_vector_sum = tuple(
                map(sum, zip(direction.value, maybe_new_direction.value))
            )
            if direction_vector_sum != (0, 0):
                set_direction(maybe_new_direction)

    snake, set_snake = idom.hooks.use_state(
        [
            (grid_size // 2 - 1, grid_size // 2 - 1),
            (grid_size // 2 - 1, grid_size // 2 - 1),
            (grid_size // 2 - 1, grid_size // 2 - 1),
        ]
    )

    grid = create_grid(grid_events, grid_size, block_size)

    for location in snake:
        set_grid_block_color(grid, location, "white")

    if snake[-1] in snake[:-1]:
        set_grid_block_color(grid, snake[-1], "red")
    elif len(snake) == grid_size ** 2:
        set_grid_block_color(grid, snake[-1], "yellow")
        return grid

    food, set_food = use_snake_food(grid_size, snake)

    new_snake_head = (
        # grid wraps due to mod op here
        (snake[-1][0] + direction.value[0]) % grid_size,
        (snake[-1][1] + direction.value[1]) % grid_size,
    )

    if snake[-1] == food:
        set_food()
        new_snake = snake + [new_snake_head]
    else:
        set_grid_block_color(grid, food, "blue")
        new_snake = snake[1:] + [new_snake_head]

    set_snake(new_snake)

    return grid


def use_snake_food(grid_size, current_snake):
    grid_points = {(x, y) for x in range(grid_size) for y in range(grid_size)}
    points_not_in_snake = grid_points.difference(current_snake)

    def random_point_not_in_snake():
        return random.choice(list(points_not_in_snake))

    food, _set_food = idom.hooks.use_state(random_point_not_in_snake)

    def set_food():
        _set_food(random_point_not_in_snake())

    return food, set_food


def create_grid(events, grid_size, block_size):
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
                [create_grid_block("black", block_size) for i in range(grid_size)],
            )
            for i in range(grid_size)
        ],
        event_handlers=events,
    )


def create_grid_block(color, block_size):
    return idom.html.div(
        {
            "style": {
                "height": f"{block_size - 4}px",
                "width": f"{block_size - 4}px",
                "backgroundColor": color,
                "display": "inline-block",
                "border": "1px solid grey",
                "box-sizing": "border-box",
            }
        }
    )


def set_grid_block_color(grid, point, color):
    x, y = point
    block = grid["children"][x]["children"][y]
    block["attributes"]["style"]["backgroundColor"] = color


import webbrowser

webbrowser.open("http://example.com")

