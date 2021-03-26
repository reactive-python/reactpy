import os

from docutils.nodes import raw
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx


_IDOM_EXAMPLE_HOST = os.environ.get("IDOM_DOC_EXAMPLE_SERVER_HOST", "")
_IDOM_EXAMPLE_PATH = os.environ.get("IDOM_DOC_EXAMPLE_SERVER_PATH", "/_idom")
_IDOM_STATIC_HOST = os.environ.get("IDOM_DOC_STATIC_SERVER_HOST", "/docs").rstrip("/")


class IteractiveWidget(Directive):

    has_content = False
    required_arguments = 1
    _next_id = 0

    def run(self):
        IteractiveWidget._next_id += 1
        container_id = f"idom-widget-{IteractiveWidget._next_id}"
        view_id = self.arguments[0]
        return [
            raw(
                "",
                f"""
                <div>
                    <div id="{container_id}" class="interactive widget-container center-content" style="" />
                    <script async type="module">
                        import loadWidgetExample from "{_IDOM_STATIC_HOST}/_static/js/load-widget-example.js";
                        loadWidgetExample("{_IDOM_EXAMPLE_HOST}", "{_IDOM_EXAMPLE_PATH}", "{container_id}", "{view_id}");
                    </script>
                </div>
                """,
                format="html",
            )
        ]


def setup(app: Sphinx) -> None:
    app.add_directive("interactive-widget", IteractiveWidget)
