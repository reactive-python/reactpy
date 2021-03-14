import os

from docutils.nodes import raw
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx


_IDOM_SERVER_LOC = os.environ.get("IDOM_DOC_EXAMPLE_SERVER_HOST", "")


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
                        import loadWidgetExample from "/docs/_static/js/load-widget-example.js";
                        loadWidgetExample("{_IDOM_SERVER_LOC}", "/_idom", "{container_id}", "{view_id}");
                    </script>
                </div>
                """,
                format="html",
            )
        ]


def setup(app: Sphinx) -> None:
    app.add_directive("interactive-widget", IteractiveWidget)
