import asyncio
import enum
import random
import time
from dataclasses import dataclass, replace

import idom


class GameState(enum.Enum):
    init = 0
    lost = 1
    won = 2
    play = 3


@idom.component
class GameView:

    state = GameState.init

    def render(self):
        if self.state == GameState.play:
            return GameLoop(self, grid_size=6, block_scale=50)

        start_button = idom.html.button(
            {"onClick": lambda event: idom.set_state(self, GameState.play)},
            "Start",
        )

        if self.state == GameState.won:
            menu = idom.html.div(idom.html.h3("You won!"), start_button)
        elif self.state == GameState.lost:
            menu = idom.html.div(idom.html.h3("You lost"), start_button)
        else:
            menu = idom.html.div(idom.html.h3("Click to play"), start_button)

        menu_style = idom.html.style(
            """
            .snake-game-menu h3 {
                margin-top: 0px !important;
            }
            """
        )

        return idom.html.div({"className": "snake-game-menu"}, menu_style, menu)


class Direction(enum.Enum):
    ArrowUp = (0, -1)
    ArrowLeft = (-1, 0)
    ArrowDown = (0, 1)
    ArrowRight = (1, 0)


@dataclass(frozen=True)
class GameLoopState:
    direction: tuple[int, int]
    snake: list[tuple[int, int]]
    food: tuple[int, int]


@idom.component
class GameLoop:
    def __init__(self, game_view, grid_size, block_scale):
        self.game_view = game_view
        self.grid_size = grid_size
        self.block_scale = block_scale
        self.new_game_state = GameState.play

    @property
    def state(self):
        return GameLoopState(
            direction=idom.Ref(Direction.ArrowRight.value),
            snake=[(self.grid_size // 2 - 1, self.grid_size // 2 - 1)],
            food=(self.grid_size // 2 - 1, self.grid_size // 2 - 1),
        )

    def render(self):
        self.frame_start_time = time.time()

        # we `use_ref` here to capture the latest direction press without any delay
        direction = self.state.direction
        # capture the last direction of travel that was rendered
        last_direction = direction.current

        grid = create_grid(self.grid_size, self.block_scale)

        @idom.event(prevent_default=True)
        def on_direction_change(event):
            if hasattr(Direction, event["key"]):
                maybe_new_direction = Direction[event["key"]].value
                direction_vector_sum = tuple(
                    map(sum, zip(last_direction, maybe_new_direction))
                )
                if direction_vector_sum != (0, 0):
                    direction.current = maybe_new_direction

        grid_wrapper = idom.html.div({"onKeyDown": on_direction_change}, grid)

        assign_grid_block_color(grid, self.state.food, "blue")

        for location in self.state.snake:
            assign_grid_block_color(grid, location, "white")

        if self.state.snake[-1] in self.state.snake[:-1]:
            assign_grid_block_color(grid, self.state.snake[-1], "red")
            self.new_game_state = GameState.lost
        elif len(self.state.snake) == self.grid_size ** 2:
            assign_grid_block_color(grid, self.state.snake[-1], "yellow")
            self.new_game_state = GameState.won

        return grid_wrapper

    async def render_effect(self):
        if self.new_game_state != GameState.play:
            await asyncio.sleep(1)
            idom.set_state(self.game_view, self.new_game_state)
            return

        frame_rate = 0.5
        render_time = time.time() - self.frame_start_time
        await asyncio.sleep(frame_rate - render_time)

        new_snake_head = (
            # grid wraps due to mod op here
            (self.state.snake[-1][0] + self.state.direction.current[0])
            % self.grid_size,
            (self.state.snake[-1][1] + self.state.direction.current[1])
            % self.grid_size,
        )

        new_state = self.state
        if self.state.snake[-1] == self.state.food:
            new_state = set_food(self.state, self.grid_size)
            new_snake = self.state.snake + [new_snake_head]
        else:
            new_snake = self.state.snake[1:] + [new_snake_head]

        new_state = replace(new_state, snake=new_snake)
        idom.set_state(self, new_state)


def set_food(state, grid_size):
    grid_points = {(x, y) for x in range(grid_size) for y in range(grid_size)}
    points_not_in_snake = grid_points.difference(state.snake)
    new_food = random.choice(list(points_not_in_snake))
    return replace(state, food=new_food)


def create_grid(grid_size, block_scale):
    return idom.html.div(
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
            "tabIndex": -1,
        },
        [
            idom.html.div(
                {"style": {"height": f"{block_scale}px"}},
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
                "outline": "1px solid grey",
            }
        }
    )


def assign_grid_block_color(grid, point, color):
    x, y = point
    block = grid["children"][x]["children"][y]
    block["attributes"]["style"]["backgroundColor"] = color


idom.run(GameView, port=8000)
