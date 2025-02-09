from typing import ClassVar
from uuid import uuid4

from jinja2_simple_tags import StandaloneTag

from reactpy.executors.utils import server_side_component_html
from reactpy.pyscript.utils import pyscript_component_html, pyscript_setup_html


class Jinja(StandaloneTag):  # type: ignore
    safe_output = True
    tags: ClassVar[set[str]] = {"component", "pyscript_component", "pyscript_setup"}

    def render(self, *args: str, **kwargs: str) -> str:
        if self.tag_name == "component":
            return component(*args, **kwargs)

        if self.tag_name == "pyscript_component":
            return pyscript_component(*args, **kwargs)

        if self.tag_name == "pyscript_setup":
            return pyscript_setup(*args, **kwargs)

        # This should never happen, but we validate it for safety.
        raise ValueError(f"Unknown tag: {self.tag_name}")  # pragma: no cover


def component(dotted_path: str, **kwargs: str) -> str:
    class_ = kwargs.pop("class", "")
    if kwargs:
        raise ValueError(f"Unexpected keyword arguments: {', '.join(kwargs)}")
    return server_side_component_html(
        element_id=uuid4().hex, class_=class_, component_path=f"{dotted_path}/"
    )


def pyscript_component(*file_paths: str, initial: str = "", root: str = "root") -> str:
    return pyscript_component_html(file_paths=file_paths, initial=initial, root=root)


def pyscript_setup(*extra_py: str, extra_js: str = "", config: str = "") -> str:
    return pyscript_setup_html(extra_py=extra_py, extra_js=extra_js, config=config)
