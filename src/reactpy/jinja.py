from typing import ClassVar
from uuid import uuid4

from jinja2_simple_tags import StandaloneTag

from reactpy.pyscript.utils import (
    pyscript_component_html,
    pyscript_setup_html,
)
from reactpy.utils import asgi_component_html


class Component(StandaloneTag):  # type: ignore
    safe_output = True
    tags: ClassVar[set[str]] = {"component"}

    def render(self, dotted_path: str, **kwargs: str) -> str:
        return asgi_component_html(
            element_id=uuid4().hex,
            class_=kwargs.pop("class", ""),
            component_path=f"{dotted_path}/",
        )


class PyScriptComponent(StandaloneTag):  # type: ignore
    safe_output = True
    tags: ClassVar[set[str]] = {"pyscript_component"}

    def render(self, *file_paths: str, initial: str = "", root: str = "root") -> str:
        return pyscript_component_html(
            file_paths=file_paths, initial=initial, root=root
        )


class PyScriptSetup(StandaloneTag):  # type: ignore
    safe_output = True
    tags: ClassVar[set[str]] = {"pyscript_setup"}

    def render(
        self, *extra_py: str, extra_js: str | dict = "", config: str | dict = ""
    ) -> str:
        """
        Args:
            extra_py: Dependencies that need to be loaded on the page for \
                your PyScript components. Each dependency must be contained \
                within it's own string and written in Python requirements file syntax.

        Kwargs:
            extra_js: A JSON string or Python dictionary containing a vanilla \
                JavaScript module URL and the `name: str` to access it within \
                `pyscript.js_modules.*`.
            config: A JSON string or Python dictionary containing PyScript \
                configuration values.
        """

        return pyscript_setup_html(extra_py=extra_py, extra_js=extra_js, config=config)
