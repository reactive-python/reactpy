from pathlib import Path

from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx_panels.tabs import TabbedDirective

here = Path(__file__).parent
examples = here.parent / "examples"


class WidgetExample(SphinxDirective):

    has_content = False
    required_arguments = 1
    _next_id = 0

    option_spec = {"linenos": directives.flag}

    def run(self):
        example_name = self.arguments[0]
        show_linenos = "linenos" in self.options

        py_ex_path = examples / f"{example_name}.py"
        if not py_ex_path.exists():
            src_file, line_num = self.get_source_info()
            raise ValueError(
                f"Missing example file named {py_ex_path} referenced by document {src_file}:{line_num}"
            )

        py_code_tab = TabbedDirective(
            "WidgetExample",
            ["Python Code"],
            {},
            _literal_include_py_lines(
                name=example_name,
                linenos=show_linenos,
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
                _literal_include_js_lines(
                    name=example_name,
                    linenos=show_linenos,
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
            _string_to_nested_lines(
                _interactive_widget_template.format(name=example_name)
            ),
            self.lineno - 1,
            self.content_offset,
            "",
            self.state,
            self.state_machine,
        ).run()

        return py_code_tab + js_code_tab + example_tab


def _literal_include_py_lines(name, linenos):
    return _string_to_nested_lines(
        _literal_include_template.format(
            name=name,
            ext="py",
            language="python",
            linenos=":linenos:" if linenos else "",
        )
    )


def _literal_include_js_lines(name, linenos):
    return _string_to_nested_lines(
        _literal_include_template.format(
            name=name,
            ext="js",
            language="javascript",
            linenos=":linenos:" if linenos else "",
        )
    )


_interactive_widget_template = """
.. interactive-widget:: {name}
"""


_literal_include_template = """
.. literalinclude:: /examples/{name}.{ext}
    :language: {language}
    {linenos}
"""


def _string_to_nested_lines(content):
    return StringList(content.split("\n"))


def setup(app: Sphinx) -> None:
    app.add_directive("example", WidgetExample)
