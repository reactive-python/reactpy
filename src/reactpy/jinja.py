import urllib.parse
from importlib import import_module
from typing import ClassVar
from uuid import uuid4

from jinja2_simple_tags import StandaloneTag

from reactpy.utils import render_reactpy_template

try:
    import_module("jinja2")
except ImportError as e:
    raise ImportError(
        "The Jinja2 library is required to use the ReactPy template tag. "
        "Please install it via `pip install reactpy[jinja]`."
    ) from e


class ReactPyTemplateTag(StandaloneTag):
    """This allows enables a `component` tag to be used in any Jinja2 rendering context,
    as long as this template tag is registered as a Jinja2 extension."""

    safe_output = True
    tags: ClassVar[set[str]] = {"component"}

    def render(self, dotted_path: str, *args, **kwargs):
        uuid = uuid4().hex
        class_ = kwargs.pop("class", "")
        kwargs.pop("key", "")  # `key` is effectively useless for the root node

        # Generate the websocket URL
        append_component_path = f"{dotted_path}/"
        if kwargs.get("args") is not None:
            raise ValueError("Cannot specify `args` as a keyword argument")
        if args:
            kwargs["args"] = args
        if kwargs:
            append_component_path += f"?{urllib.parse.urlencode(kwargs)}"

        return render_reactpy_template(uuid, class_, append_component_path)
