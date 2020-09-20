from pathlib import Path

from sphinx.application import Sphinx
from docutils.parsers.rst import Directive
from docutils.statemachine import StringList

from sphinx_panels.tabs import TabbedDirective

here = Path(__file__).parent
examples = here.parent / "examples"


class WidgetExample(Directive):

    has_content = False
    required_arguments = 1
    _next_id = 0

    def run(self):
        example_name = self.arguments[0]

        py_code_tab = TabbedDirective(
            "WidgetExample",
            ["Python Code"],
            {},
            StringList(
                [
                    "",
                    f"    .. literalinclude:: examples/{example_name}.py",
                    "",
                ]
            ),
            self.lineno - 1,
            self.content_offset,
            "",
            self.state,
            self.state_machine,
        ).run()

        if (examples / f"{example_name}.js").exists():
            js_code_tab = TabbedDirective(
                "WidgetExample",
                ["Javascript Code"],
                {},
                StringList(
                    [
                        "",
                        f"    .. literalinclude:: examples/{example_name}.js",
                        "        :language: javascript",
                        "",
                    ]
                ),
                self.lineno - 1,
                self.content_offset,
                "",
                self.state,
                self.state_machine,
            ).run()
        else:
            js_code_tab = []

        example_tab = TabbedDirective(
            "WidgetExample",
            ["Live Example"],
            {},
            StringList(
                [
                    "",
                    f"    .. interactive-widget:: {example_name}",
                    "",
                ]
            ),
            self.lineno - 1,
            self.content_offset,
            "",
            self.state,
            self.state_machine,
        ).run()

        return py_code_tab + js_code_tab + example_tab


def setup(app: Sphinx) -> None:
    app.add_directive("example", WidgetExample)
