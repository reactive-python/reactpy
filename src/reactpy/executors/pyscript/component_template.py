# ruff: noqa: N816, RUF006
# type: ignore
import asyncio

from reactpy.executors.pyscript.layout_handler import ReactPyLayoutHandler


# User component is inserted below by regex replacement
def user_workspace_UUID():
    """Encapsulate the user's code with a completely unique function (workspace)
    to prevent overlapping imports and variable names between different components.

    This code is designed to be run directly by PyScript, and is not intended to be run
    in a normal Python environment.

    ReactPy-Django performs string substitutions to turn this file into valid PyScript.
    """

    def root(): ...

    return root()


# Create a task to run the user's component workspace
task_UUID = asyncio.create_task(ReactPyLayoutHandler("UUID").run(user_workspace_UUID))
