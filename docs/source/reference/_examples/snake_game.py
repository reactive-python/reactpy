import asyncio
import enum
import random
import time

import reactpy


class GameState(enum.Enum):
    init = 0
    lost = 1
    won = 2
    play = 3


@reactpy.component
def GameView():
    game_state, set_game_state = reactpy.hooks.use_state(GameState.init)

    if game_state == GameState.play:
        return GameLoop(grid_size=6, block_scale=50, set_game_state=set_game_state)

    start_button = reactpy.html.button(
        {"on_click": lambda event: set_game_state(GameState.play)}, "Start"
    )

    if game_state == GameState.won:
        menu = reactpy.html.div(reactpy.html.h3("You won!"), start_button)
    elif game_state == GameState.lost:
        menu = reactpy.html.div(reactpy.html.h3("You lost"), start_button)
    else:
        menu = reactpy.html.div(reactpy.html.h3("Click to play"), start_button)

    menu_style = reactpy.html.style(
        """
        .snake-game-menu h3 {
            margin-top: 0px !important;
        }
        """
    )

    return reactpy.html.div({"class_name": "snake-game-menu"}, menu_style, menu)


class Direction(enum.Enum):
    ArrowUp = (0, -1)
    ArrowLeft = (-1, 0)
    ArrowDown = (0, 1)
    ArrowRight = (1, 0)


@reactpy.component
def GameLoop(grid_size, block_scale, set_game_state):
    # we `use_ref` here to capture the latest direction press without any delay
    direction = reactpy.hooks.use_ref(Direction.ArrowRight.value)
    # capture the last direction of travel that was rendered
    last_direction = direction.current

    snake, set_snake = reactpy.hooks.use_state(
        [(grid_size // 2 - 1, grid_size // 2 - 1)]
    )
    food, set_food = use_snake_food(grid_size, snake)

    grid = create_grid(grid_size, block_scale)

    @reactpy.event(prevent_default=True)
    def on_direction_change(event):
        if hasattr(Direction, event["key"]):
            maybe_new_direction = Direction[event["key"]].value
            direction_vector_sum = tuple(
                map(sum, zip(last_direction, maybe_new_direction, strict=False))
            )
            if direction_vector_sum != (0, 0):
                direction.current = maybe_new_direction

    grid_wrapper = reactpy.html.div({"on_key_down": on_direction_change}, grid)

    assign_grid_block_color(grid, food, "blue")

    for location in snake:
        assign_grid_block_color(grid, location, "white")

    new_game_state = None
    if snake[-1] in snake[:-1]:
        assign_grid_block_color(grid, snake[-1], "red")
        new_game_state = GameState.lost
    elif len(snake) == grid_size**2:
        assign_grid_block_color(grid, snake[-1], "yellow")
        new_game_state = GameState.won

    interval = use_interval(0.5)

    @reactpy.hooks.use_async_effect
    async def animate():
        if new_game_state is not None:
            await asyncio.sleep(1)
            set_game_state(new_game_state)
            return

        await interval

        new_snake_head = (
            # grid wraps due to mod op here
            (snake[-1][0] + direction.current[0]) % grid_size,
            (snake[-1][1] + direction.current[1]) % grid_size,
        )

        if snake[-1] == food:
            set_food()
            new_snake = [*snake, new_snake_head]
        else:
            new_snake = [*snake[1:], new_snake_head]

        set_snake(new_snake)

    return grid_wrapper


def use_snake_food(grid_size, current_snake):
    grid_points = {(x, y) for x in range(grid_size) for y in range(grid_size)}
    points_not_in_snake = grid_points.difference(current_snake)

    food, _set_food = reactpy.hooks.use_state(current_snake[-1])

    def set_food():
        _set_food(random.choice(list(points_not_in_snake)))

    return food, set_food


def use_interval(rate):
    usage_time = reactpy.hooks.use_ref(time.time())

    async def interval() -> None:
        await asyncio.sleep(rate - (time.time() - usage_time.current))
        usage_time.current = time.time()

    return asyncio.ensure_future(interval())


def create_grid(grid_size, block_scale):
    return reactpy.html.div(
        {
            "style": {
                "height": f"{block_scale * grid_size}px",
                "width": f"{block_scale * grid_size}px",
                "cursor": "pointer",
                "display": "grid",
                "grid-gap": 0,
                "grid-template-columns": f"repeat({grid_size}, {block_scale}px)",
                "grid-template-rows": f"repeat({grid_size}, {block_scale}px)",
            },
            "tab_index": -1,
        },
        [
            reactpy.html.div(
                {"style": {"height": f"{block_scale}px"}, "key": i},
                [
                    create_grid_block("black", block_scale, key=i)
                    for i in range(grid_size)
                ],
            )
            for i in range(grid_size)
        ],
    )


def create_grid_block(color, block_scale, key):
    return reactpy.html.div(
        {
            "style": {
                "height": f"{block_scale}px",
                "width": f"{block_scale}px",
                "background_color": color,
                "outline": "1px solid grey",
            },
            "key": key,
        }
    )


def assign_grid_block_color(grid, point, color):
    x, y = point
    block = grid["children"][x]["children"][y]
    block["attributes"]["style"]["backgroundColor"] = color


reactpy.run(GameView)
