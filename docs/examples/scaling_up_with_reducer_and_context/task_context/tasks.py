"""The reducer, the context, and the initial state — all outside the UI."""

from collections.abc import Callable
from typing import Any

from reactpy import create_context
from reactpy.types import Context

TaskState = dict[str, Any]
TaskValue = tuple[TaskState, Callable[[dict[str, Any]], None]]

# The reducer never mutates what it is given, so one shared constant is
# safe as the initial state for every instance.
INITIAL_TASKS = [
    {"id": 0, "text": "Packing", "done": False},
    {"id": 1, "text": "Passport", "done": True},
]

INITIAL_STATE: TaskState = {"tasks": INITIAL_TASKS, "next_id": 2}

# One context carries both halves: the state to read and the dispatch to change
# it with. Annotate the name, or the default narrows the value type.
TaskContext: Context[TaskValue] = create_context((INITIAL_STATE, lambda action: None))


def tasks_reducer(state: TaskState, action: dict[str, Any]) -> TaskState:
    kind = action["type"]
    if kind == "added":
        task = {"id": state["next_id"], "text": "New task", "done": False}
        return {
            **state,
            "tasks": [*state["tasks"], task],
            "next_id": state["next_id"] + 1,
        }
    if kind == "toggled":
        return {
            **state,
            "tasks": [
                {**task, "done": not task["done"]}
                if task["id"] == action["id"]
                else task
                for task in state["tasks"]
            ],
        }
    if kind == "deleted":
        return {
            **state,
            "tasks": [task for task in state["tasks"] if task["id"] != action["id"]],
        }
    raise ValueError(f"unknown action type {kind!r}")
