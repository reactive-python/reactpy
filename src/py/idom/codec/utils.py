import re
from typing import Callable, Any, Optional, Tuple, List


def transform_string(
    string: str,
    transform: Callable[[str, int, Any], Tuple[int, Optional[str]]],
    state: Any = None,
) -> str:
    """Apply a transformation function to a string and return the result.

    Parameters:
        string:
            The string to transform
        transform:
            The function applied to the string. Accepts three arguments
            ``(text, string, state)`` where ``string`` and ``state`` are the same
            as from :func:`transform_string` and ``index`` is the current position
            within the ``string``. The function should return a tuple of the form
            ``(next_index, replacement)`` where ``next_index`` is the next index
            to jump to in the ``string`` and ``replacement`` is a string that should
            replace the section of ``string`` from ``index`` to ``next_index``. If
            ``replacement`` is None, then the section is not altered.
        state:
            An object useful in keeping track of transformation state.
    """
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


_str_positional_formats = re.compile(r"[^\{]?(\{\d+\})[^\}]?")


def split_str_positional_format(string: str) -> List[Tuple[bool, str]]:
    result = []
    last = 0
    for match in _str_positional_formats.finditer(string):
        start, stop = match.span(1)
        if last != start:
            # outside expression
            result.append((False, string[last:start]))
        # inside expression
        result.append((True, string[start:stop]))
        last = stop
    if last != len(string):
        result.append((False, string[last:]))
    return result


def split_fstr_style_exprs(string: str) -> List[Tuple[bool, str]]:
    """Split string on f-string style expressions.

    Parameters:
        string: The string to split.

    Returns:
        A list of tuples with a boolean and string. In the tuple a boolean
        indicates whether the string is in an f-string expression or not.
    """
    result = []
    last = stop = 0
    for start, stop in _expr_starts_and_stops(str(string)):
        if last != start:
            # outside expression
            result.append((False, string[last : start - 1]))
        # inside expression
        result.append((True, string[start:stop]))
        last = stop + 1
    if last != len(string):
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
                    msg = "Mismatched parentheses in VDOM-string"
                    _raise_syntax_error(string, msg, index + 1)
        index += 1

    if brace_depth:
        offset = len(string) + 1
        _raise_syntax_error(string, "Mismatched braces in VDOM-string.", offset)

    return list(zip(expression_starts, expression_stops))


def _raise_syntax_error(template: str, message: str, offset: int = 1) -> None:
    info = ("vdom-syntax-transpiler", 1, offset, template)
    raise SyntaxError(message, info)
