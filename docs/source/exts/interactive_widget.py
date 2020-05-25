from sphinx.application import Sphinx
from docutils.parsers.rst import Directive
from docutils.nodes import raw


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
                <div style="margin-bottom:25px">
                    <div id="{container_id}" />
                    <script async type="module">
                        import {{ renderLayout }} from "/client/core_modules/layout.js";
                        const loc = window.location;
                        const idom_url = "//" + loc.host;
                        const http_proto = loc.protocol;
                        const ws_proto = (http_proto === "https:") ? "wss:" : "ws:";
                        renderLayout(
                            document.getElementById("{container_id}"),
                            ws_proto + idom_url + "/stream?view_id={view_id}"
                        );
                    </script>
                </div>
                """,
                format="html",
            )
        ]


def setup(app: Sphinx) -> None:
    app.add_directive("interactive-widget", IteractiveWidget)
