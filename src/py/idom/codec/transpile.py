from html.parser import HTMLParser as _HtmlParser
from io import StringIO
from typing import Any, Callable, Tuple, Optional, Sequence, List


def transpile_html_templates(text: str) -> str:
    return _transform_string(
        text.strip(), _transpile_html_templates, TemplateTranspiler()
    )


class TemplateTranspiler(_HtmlParser):
    def transpile(self, text: str) -> str:
        self.feed(text)
        code = self.code()
        self.reset()
        return code

    def code(self) -> str:
        self._code.seek(0)
        value = self._code.read()
        self._code.seek(self._cursor)
        return value[:-2]

    def reset(self) -> None:
        super().reset()
        self._cursor = 0
        self._code = StringIO()

    def handle_starttag(
        self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]
    ) -> None:
        self._write(f"idom.vdom({self._substitute_variables(tag)}, " + "{")
        subbed_attrs = [
            (
                self._substitute_variables(k),
                self._substitute_variables("true" if v is None else v),
            )
            for k, v in attrs
        ]
        self._write(", ".join("%s: %s" % item for item in subbed_attrs))
        self._write("}, [")

    def handle_data(self, data: str) -> None:
        self._write(self._substitute_variables(data) + ", ")

    def handle_endtag(self, tag: str) -> None:
        self._write("]), ")

    def handle_startendtag(self, tag: str, attrs: Sequence[Tuple[str, str]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def _write(self, text: str) -> None:
        self._cursor += self._code.write(text)
        self._code.seek(self._cursor)

    @staticmethod
    def _substitute_variables(text: str) -> str:
        parts: List[Tuple[int, int]] = []
        index = 0
        sub_start = 0
        in_var = False

        while index < len(text):
            if text[index : index + 2] in ("{{", "}}"):
                index += 2
                continue
            if not in_var:
                if text[index] == "{":
                    in_var = True
                    sub_start = index
                    index += 1
                    continue
            else:
                if text[index] == "}":
                    in_var = False
                    parts.append((sub_start, index + 1))
                    index += 1
                    continue
            index += 1

        code = ""
        last_stop = 0
        for start, stop in parts:
            code += repr(text[last_stop:start])
            code += text[start + 1 : stop - 1]
            last_stop = stop
        code += repr(text[last_stop:])

        return code


def _transpile_html_templates(
    text: str, index: int, transpiler: TemplateTranspiler
) -> Tuple[int, Optional[str]]:
    if text[index : index + 4] != "html":
        return index + 1, None

    index += 4

    for str_char in ('"""', '"', "'''", "'"):
        # characters open a string
        if text[index : index + len(str_char)] == str_char:
            break
    else:
        return index + 1, None

    for forward_index in range(index + 1, len(text)):
        if text[forward_index : forward_index + len(str_char)] == str_char:
            template = text[index + len(str_char) : forward_index]
            py_code = transpiler.transpile(template.strip())
            return forward_index + len(str_char), py_code

    return forward_index + len(str_char), None


def _transform_string(
    string: str,
    transform: Callable[[str, int, Any], Tuple[int, Optional[str]]],
    state: Any = None,
) -> str:
    index = 0
    changes = []

    # find changes to make
    while index < len(string):
        next_index, new = transform(string, index, state)
        if new is not None:
            changes.append((index, next_index, new))
        index = next_index

    # apply changes
    for start, stop, new in reversed(changes):
        string = string[:start] + new + string[stop:]

    return string
