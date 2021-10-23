from pathlib import Path

from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx_design.tabs import TabSetDirective


here = Path(__file__).parent
examples = here.parent / "_examples"


class WidgetExample(SphinxDirective):

    has_content = False
    required_arguments = 1
    _next_id = 0

    option_spec = {
        "linenos": directives.flag,
        "live-example-is-default-tab": directives.flag,
    }

    def run(self):
        example_name = self.arguments[0]
        show_linenos = "linenos" in self.options

        py_ex_path = examples / f"{example_name}.py"
        if not py_ex_path.exists():
            src_file, line_num = self.get_source_info()
            raise ValueError(
                f"Missing example file named {py_ex_path} referenced by document {src_file}:{line_num}"
            )

        labeled_tab_items = {
            "Python Code": _literal_include_py(
                name=example_name,
                linenos=show_linenos,
            ),
            "Live Example": _interactive_widget(
                name=example_name,
                with_activate_button="live-example-is-default-tab" not in self.options,
            ),
        }

        if (examples / f"{example_name}.js").exists():
            labeled_tab_items["Javascript Code"] = _literal_include_js(
                name=example_name,
                linenos=show_linenos,
            )

        tab_label_order = (
            ["Live Example", "Python Code", "Javascript Code"]
            if "live-example-is-default-tab" in self.options
            else ["Python Code", "Javascript Code", "Live Example"]
        )

        return TabSetDirective(
            "WidgetExample",
            [],
            {},
            _make_tab_items(
                [
                    (label, labeled_tab_items[label])
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


def _literal_include_py(name, linenos):
    return _literal_include_template.format(
        name=name,
        ext="py",
        language="python",
        linenos=":linenos:" if linenos else "",
    )


def _literal_include_js(name, linenos):
    return _literal_include_template.format(
        name=name,
        ext="js",
        language="javascript",
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
.. literalinclude:: /_examples/{name}.{ext}
    :language: {language}
    {linenos}
"""


def _string_to_nested_lines(content):
    return StringList(content.split("\n"))


def setup(app: Sphinx) -> None:
    app.add_directive("example", WidgetExample)
