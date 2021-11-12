from pathlib import Path

from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx_design.tabs import TabSetDirective

from docs.examples import get_js_example_file_by_name, get_py_example_file_by_name


HERE = Path(__file__)
EXAMPLES_DIR = HERE.parent.parent / "_examples"


class WidgetExample(SphinxDirective):

    has_content = False
    required_arguments = 1
    _next_id = 0

    option_spec = {
        "linenos": directives.flag,
        "result-is-default-tab": directives.flag,
        "activate-result": directives.flag,
    }

    def run(self):
        example_name = self.arguments[0]
        show_linenos = "linenos" in self.options
        live_example_is_default_tab = "result-is-default-tab" in self.options
        activate_result = "activate-result" in self.options

        py_ex_path = get_py_example_file_by_name(example_name)
        if not py_ex_path.exists():
            src_file, line_num = self.get_source_info()
            raise ValueError(
                f"Missing example file named {py_ex_path} referenced by document {src_file}:{line_num}"
            )

        labeled_tab_items = {
            "python": _literal_include(
                name=str(py_ex_path.relative_to(EXAMPLES_DIR)),
                linenos=show_linenos,
            ),
            "result": _interactive_widget(
                name=example_name,
                with_activate_button=not activate_result,
            ),
        }

        labeled_tab_titles = {
            "python": "Python",
            "javascript": "Javascript",
            "result": "▶️ Result",
        }

        js_ex_path = get_js_example_file_by_name(example_name)
        if js_ex_path.exists():
            labeled_tab_items["javascript"] = _literal_include(
                name=str(js_ex_path.relative_to(EXAMPLES_DIR)),
                linenos=show_linenos,
            )

        tab_label_order = (
            ["result", "python", "javascript"]
            if live_example_is_default_tab
            else ["python", "javascript", "result"]
        )

        return TabSetDirective(
            "WidgetExample",
            [],
            {},
            _make_tab_items(
                [
                    (labeled_tab_titles[label], labeled_tab_items[label])
                    for label in tab_label_order
                    if label in labeled_tab_items
                ]
            ),
            self.lineno - 1,
            self.content_offset,
            "",
            self.state,
            self.state_machine,
        ).run()


def _make_tab_items(labeled_content_tuples):
    tab_items = ""
    for label, content in labeled_content_tuples:
        tab_items += _tab_item_template.format(
            label=label,
            content=content.replace("\n", "\n    "),
        )
    return _string_to_nested_lines(tab_items)


def _literal_include(name, linenos):
    if name.endswith(".py"):
        language = "python"
    elif name.endswith(".js"):
        language = "javascript"
    else:
        raise ValueError("Unknown extension type")

    return _literal_include_template.format(
        name=name,
        language=language,
        linenos=":linenos:" if linenos else "",
    )


def _interactive_widget(name, with_activate_button):
    return _interactive_widget_template.format(
        name=name,
        activate_button_opt="" if with_activate_button else ":no-activate-button:",
    )


_tab_item_template = """
.. tab-item:: {label}

    {content}
"""


_interactive_widget_template = """
.. interactive-widget:: {name}
    {activate_button_opt}
"""


_literal_include_template = """
.. literalinclude:: /_examples/{name}
    :language: {language}
    {linenos}
"""


def _string_to_nested_lines(content):
    return StringList(content.split("\n"))


def setup(app: Sphinx) -> None:
    app.add_directive("example", WidgetExample)
