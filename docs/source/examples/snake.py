import asyncio
import enum
import random
import time

import idom


class GameState(enum.Enum):
    init = 0
    lost = 1
    won = 2
    play = 3


@idom.element
async def GameView(grid_size, block_scale):
    game_state, set_game_state = idom.hooks.use_state(GameState.init)

    if game_state == GameState.play:
        return GameLoop(grid_size, block_scale, set_game_state)

    async def start_playing(event):
        set_game_state(GameState.play)

    if game_state == GameState.won:
        await asyncio.sleep(1)
        return idom.html.div(
            idom.html.h1("You won!"),
            idom.html.button({"onClick": start_playing}, "Start"),
        )
    elif game_state == GameState.lost:
        await asyncio.sleep(1)
        return idom.html.div(
            idom.html.h1("You lost"),
            idom.html.button({"onClick": start_playing}, "Start"),
        )
    else:
        return idom.html.div(
            idom.html.h1("Click to play"),
            idom.html.button({"onClick": start_playing}, "Start"),
        )


class Direction(enum.Enum):
    ArrowUp = (-1, 0)
    ArrowLeft = (0, -1)
    ArrowDown = (1, 0)
    ArrowRight = (0, 1)


@idom.element
async def GameLoop(grid_size, block_scale, set_game_state):
    direction = idom.hooks.use_ref(Direction.ArrowRight.value)
    snake, set_snake = idom.hooks.use_state([(grid_size // 2 - 1, grid_size // 2 - 1)])
    food, set_food = use_snake_food(grid_size, snake)

    grid = create_grid(grid_size, block_scale)
    grid_events = grid["eventHandlers"] = idom.Events()

    @grid_events.on("KeyDown", prevent_default=True)
    async def on_direction_change(event):
        if hasattr(Direction, event["key"]):
            maybe_new_direction = Direction[event["key"]].value
            direction_vector_sum = tuple(
                map(sum, zip(direction.current, maybe_new_direction))
            )
            if direction_vector_sum != (0, 0):
                direction.current = maybe_new_direction

    assign_grid_block_color(grid, food, "blue")

    for location in snake:
        assign_grid_block_color(grid, location, "white")

    if snake[-1] in snake[:-1]:
        assign_grid_block_color(grid, snake[-1], "red")
        set_game_state(GameState.lost)
    elif len(snake) == grid_size ** 2:
        assign_grid_block_color(grid, snake[-1], "yellow")
        set_game_state(GameState.won)

    interval = use_interval(0.5)

    @idom.hooks.use_effect
    async def animate():
        try:
            await interval
        except Exception as e:
            print(e)

        new_snake_head = (
            # grid wraps due to mod op here
            (snake[-1][0] + direction.current[0]) % grid_size,
            (snake[-1][1] + direction.current[1]) % grid_size,
        )

        if snake[-1] == food:
            set_food()
            new_snake = snake + [new_snake_head]
        else:
            new_snake = snake[1:] + [new_snake_head]

        set_snake(new_snake)

    return grid


def use_interval(rate):
    last_usage_time = idom.hooks.use_ref(time.time())

    async def interval():
        await asyncio.sleep(rate - (time.time() - last_usage_time.current))
        last_usage_time.current = time.time()

    return interval()


def use_snake_food(grid_size, current_snake):
    grid_points = {(x, y) for x in range(grid_size) for y in range(grid_size)}
    points_not_in_snake = grid_points.difference(current_snake)

    food, _set_food = idom.hooks.use_state(current_snake[-1])

    def set_food():
        _set_food(random.choice(list(points_not_in_snake)))

    return food, set_food


def create_grid(grid_size, block_scale):
    return idom.html.div(
        {"style": {"height": "100%", "width": "100%"}, "tabIndex": -1},
        [
            idom.html.div(
                {"style": {"height": block_scale}},
                [create_grid_block("black", block_scale) for i in range(grid_size)],
            )
            for i in range(grid_size)
        ],
    )


def create_grid_block(color, block_scale):
    return idom.html.div(
        {
            "style": {
                "height": f"{block_scale}px",
                "width": f"{block_scale}px",
                "backgroundColor": color,
                "display": "inline-block",
                "border": "1px solid grey",
            }
        }
    )


def assign_grid_block_color(grid, point, color):
    x, y = point
    block = grid["children"][x]["children"][y]
    block["attributes"]["style"]["backgroundColor"] = color


display(GameView)
