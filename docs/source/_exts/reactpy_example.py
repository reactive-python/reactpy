from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx_design.tabs import TabSetDirective

from docs.examples import (
    SOURCE_DIR,
    get_example_files_by_name,
    get_normalized_example_name,
)


class WidgetExample(SphinxDirective):
    has_content = False
    required_arguments = 1
    _next_id = 0

    option_spec = {
        "result-is-default-tab": directives.flag,
        "activate-button": directives.flag,
    }

    def run(self):
        example_name = get_normalized_example_name(
            self.arguments[0],
            # only used if example name starts with "/"
            self.get_source_info()[0],
        )

        show_linenos = "linenos" in self.options
        live_example_is_default_tab = "result-is-default-tab" in self.options
        activate_result = "activate-button" not in self.options

        ex_files = get_example_files_by_name(example_name)
        if not ex_files:
            src_file, line_num = self.get_source_info()
            raise ValueError(
                f"Missing example named {example_name!r} "
                f"referenced by document {src_file}:{line_num}"
            )

        labeled_tab_items: list[tuple[str, Any]] = []
        if len(ex_files) == 1:
            labeled_tab_items.append(
                (
                    "main.py",
                    _literal_include(
                        path=ex_files[0],
                        linenos=show_linenos,
                    ),
                )
            )
        else:
            for path in sorted(
                ex_files, key=lambda p: "" if p.name == "main.py" else p.name
            ):
                labeled_tab_items.append(
                    (
                        path.name,
                        _literal_include(
                            path=path,
                            linenos=show_linenos,
                        ),
                    )
                )

        result_tab_item = (
            "🚀 result",
            _interactive_widget(
                name=example_name,
                with_activate_button=not activate_result,
            ),
        )
        if live_example_is_default_tab:
            labeled_tab_items.insert(0, result_tab_item)
        else:
            labeled_tab_items.append(result_tab_item)

        return TabSetDirective(
            "WidgetExample",
            [],
            {},
            _make_tab_items(labeled_tab_items),
            self.lineno - 2,
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


def _literal_include(path: Path, linenos: bool):
    try:
        language = {
            ".py": "python",
            ".js": "javascript",
            ".json": "json",
        }[path.suffix]
    except KeyError:
        raise ValueError(f"Unknown extension type {path.suffix!r}")

    return _literal_include_template.format(
        name=str(path.relative_to(SOURCE_DIR)),
        language=language,
        options=_join_options(_get_file_options(path)),
    )


def _join_options(option_strings: list[str]) -> str:
    return "\n    ".join(option_strings)


OPTION_PATTERN = re.compile(r"#\s:[\w-]+:.*")


def _get_file_options(file: Path) -> list[str]:
    options = []

    for line in file.read_text().split("\n"):
        if not line.strip():
            continue
        if not line.startswith("#"):
            break
        if not OPTION_PATTERN.match(line):
            continue
        option_string = line[1:].strip()
        if option_string:
            options.append(option_string)

    return options


def _interactive_widget(name, with_activate_button):
    return _interactive_widget_template.format(
        name=name,
        activate_button_opt=":activate-button:" if with_activate_button else "",
    )


_tab_item_template = """
.. tab-item:: {label}

    {content}
"""


_interactive_widget_template = """
.. reactpy-view:: {name}
    {activate_button_opt}
"""


_literal_include_template = """
.. literalinclude:: /{name}
    :language: {language}
    {options}
"""


def _string_to_nested_lines(content):
    return StringList(content.split("\n"))


def setup(app: Sphinx) -> None:
    app.add_directive("reactpy", WidgetExample)
