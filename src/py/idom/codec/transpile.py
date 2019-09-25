from html.parser import HTMLParser as _HtmlParser
from io import StringIO
from typing import Any, Callable, Tuple, Optional, Sequence, List


def transpile_html_templates(text: str) -> str:
    return _transform_string(
        text.strip(), _transpile_html_templates, TemplateTranspiler()
    )


class TemplateTranspiler(_HtmlParser):
    def transpile(self, text: str) -> str:
        self._feed(text)
        code = self._read_code()
        self.reset()
        return code

    def feed(self, text: str) -> None:
        raise NotImplementedError()

    def _feed(self, text: str) -> None:
        return super().feed(self._load_exprs(text))

    def _read_code(self) -> str:
        self._code.seek(0)
        value = self._code.read()
        self._code.seek(self._cursor)
        return value[:-2]

    def reset(self) -> None:
        super().reset()
        self._exprs: List[str] = []
        self._cursor = 0
        self._code = StringIO()

    def handle_starttag(
        self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]
    ) -> None:
        self._write(f"idom.vdom({self._substitute_exprs(tag)}, " + "{")
        subbed_attrs = [
            (
                self._substitute_exprs(k),
                self._substitute_exprs("true" if v is None else v),
            )
            for k, v in attrs
        ]
        self._write(", ".join("%s: %s" % item for item in subbed_attrs))
        self._write("}, [")

    def handle_data(self, data: str) -> None:
        self._write(self._substitute_exprs(data) + ", ")

    def handle_endtag(self, tag: str) -> None:
        self._write("]), ")

    def handle_startendtag(self, tag: str, attrs: Sequence[Tuple[str, str]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def _write(self, text: str) -> None:
        self._cursor += self._code.write(text)
        self._code.seek(self._cursor)

    def _load_exprs(self, text: str) -> str:
        parts: List[str] = []
        for is_expr, string in _split_fstr_style_exprs(text):
            if string:
                if is_expr:
                    parts.append(f"{{{len(self._exprs)}}}")
                    self._exprs.append(string)
                else:
                    parts.append(string)
        return "".join(parts)

    def _substitute_exprs(self, text: str) -> str:
        result = text.format(*self._exprs)
        if result == text:
            # no formating took place
            return repr(text)
        else:
            return result


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


def _split_fstr_style_exprs(string: str) -> List[Tuple[bool, str]]:
    result = []
    last = stop = 0
    for start, stop in _expr_starts_and_stops(str(string)):
        # outside expression
        result.append((False, string[last : start - 1]))
        # inside expression
        result.append((True, string[start:stop]))
        last = stop + 1
    result.append((False, string[last:]))
    return result


def _expr_starts_and_stops(string: str) -> List[Tuple[int, int]]:  # noqa: C901
    index = 0
    brace_depth = 0
    paren_depth = 0
    expression_starts = []
    expression_stops = []
    in_single_quote = False
    in_double_quote = False
    in_triple_quote = False
    in_quotes = False
    in_expression = False

    while index < len(string):
        char = string[index]
        if brace_depth > 0:
            if char == "'" and not in_double_quote:
                if string[index + 1 : index + 3] == "''":
                    in_triple_quote = not in_triple_quote
                elif not in_triple_quote:
                    in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                if string[index + 1 : index + 3] == '""':
                    in_triple_quote = not in_triple_quote
                elif not in_triple_quote:
                    in_double_quote = not in_double_quote
            in_quotes = in_double_quote or in_single_quote or in_triple_quote
        if char == "{":
            if brace_depth > 0:
                if not in_quotes:
                    # increment open count to verify ballanced braces at end
                    brace_depth += 1
            else:
                j = 0
                for j, c in enumerate(string[index + 1 :]):
                    if c != "{":
                        break
                index += j
                if j % 2 == 0:
                    # encountered odd number of open braces
                    expression_starts.append(index + 1)
                    brace_depth += 1
                    in_expression = True
        elif char == "}" and not in_quotes:
            if brace_depth > 1:
                brace_depth -= 1
            elif brace_depth == 1:
                j = 0
                for j, c in enumerate(string[index + 1 :] + " "):
                    if c != "}":
                        break
                if j % 2 == 0:
                    # encountered odd number of open braces
                    expression_stops.append(index)
                    brace_depth -= 1
                    in_expression = False
                index += j
        elif in_expression:
            if char == "(":
                paren_depth += 1
            elif char == ")":
                paren_depth -= 1
                if paren_depth < 0:
                    msg = "Mismatched parentheses in f-string"
                    _raise_syntax_error(string, msg, index + 1)
        index += 1

    if brace_depth:
        offset = len(string) + 1
        _raise_syntax_error(string, "Mismatched braces in f-string.", offset)

    return list(zip(expression_starts, expression_stops))


def _raise_syntax_error(template: str, message: str, offset: int = 1) -> None:
    info = ("idom", 1, offset, template)
    raise SyntaxError(message, info)


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
