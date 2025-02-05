from typing import ClassVar
from uuid import uuid4

from jinja2_simple_tags import StandaloneTag

from reactpy.config import REACTPY_DEBUG, REACTPY_PATH_PREFIX
from reactpy.pyscript.utils import (
    PYSCRIPT_LAYOUT_HANDLER,
    extend_pyscript_config,
    render_pyscript_template,
)
from reactpy.utils import render_mount_template


class Component(StandaloneTag):  # type: ignore
    safe_output = True
    tags: ClassVar[set[str]] = {"component"}

    def render(self, dotted_path: str, **kwargs: str) -> str:
        return render_mount_template(
            element_id=uuid4().hex,
            class_=kwargs.pop("class", ""),
            append_component_path=f"{dotted_path}/",
        )


class PyScriptComponent(StandaloneTag):  # type: ignore
    safe_output = True
    tags: ClassVar[set[str]] = {"pyscript_component"}

    def render(self, *file_paths: str, initial: str = "", root: str = "root") -> str:
        return render_pyscript_template(
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

        hide_pyscript_debugger = f'<link rel="stylesheet" href="{REACTPY_PATH_PREFIX.current}static/pyscript-hide-debug.css" />'
        pyscript_config = extend_pyscript_config(extra_py, extra_js, config)

        return (
            f'<link rel="stylesheet" href="{REACTPY_PATH_PREFIX.current}static/pyscript/core.css" />'
            f'<link rel="stylesheet" href="{REACTPY_PATH_PREFIX.current}static/pyscript-custom.css" />'
            f"{'' if REACTPY_DEBUG.current else hide_pyscript_debugger}"
            f'<script type="module" async crossorigin="anonymous" src="{REACTPY_PATH_PREFIX.current}static/pyscript/core.js">'
            "</script>"
            f'<py-script async config="{pyscript_config}">{PYSCRIPT_LAYOUT_HANDLER}</py-script>'
        )
