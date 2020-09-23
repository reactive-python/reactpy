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

        py_ex_path = examples / f"{example_name}.py"
        if not py_ex_path.exists():
            raise ValueError(f"No example file named {py_ex_path}")

        py_code_tab = TabbedDirective(
            "WidgetExample",
            ["Python Code"],
            {},
            StringList(
                [
                    "",
                    f"    .. literalinclude:: examples/{example_name}.py",
                    f"        :lines: 1-{_py_ex_file_cutoff(py_ex_path)}",
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


def _py_ex_file_cutoff(path):
    empty_line_start = None
    with path.open() as f:
        for i, l in enumerate(f):
            if not l.strip():
                if empty_line_start is None:
                    empty_line_start = i + 1
            elif l.startswith("display(") and empty_line_start is not None:
                return empty_line_start
            else:
                empty_line_start = None
    raise ValueError(f"No display function called in {path}")


def setup(app: Sphinx) -> None:
    app.add_directive("example", WidgetExample)
