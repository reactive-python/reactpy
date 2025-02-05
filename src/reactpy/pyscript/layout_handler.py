# type: ignore
import asyncio
import logging

from jsonpointer import set_pointer
from pyodide.ffi.wrappers import add_event_listener
from pyscript.js_modules import morphdom

import js
from reactpy.core.layout import Layout


class ReactPyLayoutHandler:
    """Encapsulate the entire layout handler with a class to prevent overlapping
    variable names between user code.

    This code is designed to be run directly by PyScript, and is not intended to be run
    in a normal Python environment.
    """

    def __init__(self, uuid):
        self.uuid = uuid
        self.running_tasks = set()

    @staticmethod
    def update_model(update, root_model):
        """Apply an update ReactPy's internal DOM model."""
        if update["path"]:
            set_pointer(root_model, update["path"], update["model"])
        else:
            root_model.update(update["model"])

    def render_html(self, layout, model):
        """Submit ReactPy's internal DOM model into the HTML DOM."""
        # Create a new container to render the layout into
        container = js.document.getElementById(f"pyscript-{self.uuid}")
        temp_root_container = container.cloneNode(False)
        self.build_element_tree(layout, temp_root_container, model)

        # Use morphdom to update the DOM
        morphdom.default(container, temp_root_container)

        # Remove the cloned container to prevent memory leaks
        temp_root_container.remove()

    def build_element_tree(self, layout, parent, model):
        """Recursively build an element tree, starting from the root component."""
        # If the model is a string, add it as a text node
        if isinstance(model, str):
            parent.appendChild(js.document.createTextNode(model))

        # If the model is a VdomDict, construct an element
        elif isinstance(model, dict):
            # If the model is a fragment, build the children
            if not model["tagName"]:
                for child in model.get("children", []):
                    self.build_element_tree(layout, parent, child)
                return

            # Otherwise, get the VdomDict attributes
            tag = model["tagName"]
            attributes = model.get("attributes", {})
            children = model.get("children", [])
            element = js.document.createElement(tag)

            # Set the element's HTML attributes
            for key, value in attributes.items():
                if key == "style":
                    for style_key, style_value in value.items():
                        setattr(element.style, style_key, style_value)
                elif key == "className":
                    element.className = value
                else:
                    element.setAttribute(key, value)

            # Add event handlers to the element
            for event_name, event_handler_model in model.get(
                "eventHandlers", {}
            ).items():
                self.create_event_handler(
                    layout, element, event_name, event_handler_model
                )

            # Recursively build the children
            for child in children:
                self.build_element_tree(layout, element, child)

            # Append the element to the parent
            parent.appendChild(element)

        # Unknown data type provided
        else:
            msg = f"Unknown model type: {type(model)}"
            raise TypeError(msg)

    def create_event_handler(self, layout, element, event_name, event_handler_model):
        """Create an event handler for an element. This function is used as an
        adapter between ReactPy and browser events."""
        target = event_handler_model["target"]

        def event_handler(*args):
            # When the event is triggered, deliver the event to the `Layout` within a background task
            task = asyncio.create_task(
                layout.deliver({"type": "layout-event", "target": target, "data": args})
            )
            # Store the task to prevent automatic garbage collection from killing it
            self.running_tasks.add(task)
            task.add_done_callback(self.running_tasks.remove)

        add_event_listener(element, event_name, event_handler)

    @staticmethod
    def delete_old_workspaces():
        """To prevent memory leaks, we must delete all user generated Python code when
        it is no longer in use (removed from the page). To do this, we compare what
        UUIDs exist on the DOM, versus what UUIDs exist within the PyScript global
        interpreter."""
        # Find all PyScript workspaces that are still on the page
        dom_workspaces = js.document.querySelectorAll(".pyscript")
        dom_uuids = {element.dataset.uuid for element in dom_workspaces}
        python_uuids = {
            value.split("_")[-1]
            for value in globals()
            if value.startswith("user_workspace_")
        }

        # Delete any workspaces that are no longer in use
        for uuid in python_uuids - dom_uuids:
            task_name = f"task_{uuid}"
            if task_name in globals():
                task: asyncio.Task = globals()[task_name]
                task.cancel()
                del globals()[task_name]
            else:
                logging.error("Could not auto delete PyScript task %s", task_name)

            workspace_name = f"user_workspace_{uuid}"
            if workspace_name in globals():
                del globals()[workspace_name]
            else:
                logging.error(
                    "Could not auto delete PyScript workspace %s", workspace_name
                )

    async def run(self, workspace_function):
        """Run the layout handler. This function is main executor for all user generated code."""
        self.delete_old_workspaces()
        root_model: dict = {}

        async with Layout(workspace_function()) as root_layout:
            while True:
                update = await root_layout.render()
                self.update_model(update, root_model)
                self.render_html(root_layout, root_model)
