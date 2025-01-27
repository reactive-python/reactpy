from typing import ClassVar
from uuid import uuid4

from jinja2_simple_tags import StandaloneTag

from reactpy.utils import render_mount_template


class ReactPyTemplateTag(StandaloneTag):
    """This allows enables a `component` tag to be used in any Jinja2 rendering context,
    as long as this template tag is registered as a Jinja2 extension."""

    safe_output = True
    tags: ClassVar[set[str]] = {"component"}

    def render(self, dotted_path: str, **kwargs):
        return render_mount_template(
            element_id=uuid4().hex,
            class_=kwargs.pop("class", ""),
            append_component_path=f"{dotted_path}/",
        )
