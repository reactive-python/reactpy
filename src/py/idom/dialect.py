import ast
from typing import Optional

import tagged
import htm
from pyalect import DialectError, Dialect


class HtmlDialectTranspiler(Dialect, name="html"):
    """An HTML dialect transpiler for Python."""

    def __init__(self, filename: Optional[str] = None):
        self.filename: str = filename or "<dialect: html>"

    def transform_src(self, source: str) -> str:
        return source

    def transform_ast(self, node: ast.AST) -> ast.AST:
        new_node: ast.AST = HtmlDialectNodeTransformer(self.filename).visit(node)
        return new_node


class HtmlDialectNodeTransformer(ast.NodeTransformer):
    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename

    def visit_Call(self, node: ast.Call) -> Optional[ast.AST]:
        if isinstance(node.func, ast.Name):
            if node.func.id == "html":
                if not (
                    node.keywords
                    or len(node.args) != 1
                    or not isinstance(node.args[0], ast.Str)
                ):
                    htm_string = node.args[0].s
                    try:
                        expr = self._make_htm_expr(htm_string)
                    except htm.ParseError as error:
                        raise DialectError(str(error), self.filename, node.lineno)
                    new_node = ast.parse(expr).body[0].value  # type: ignore
                    copied: ast.Call = ast.copy_location(new_node, node)
                    return self.generic_visit(copied)
        return node

    @staticmethod
    def _make_htm_expr(text: str) -> str:
        src = ""
        is_first_child = False
        strings, exprs = tagged.split(text)
        for op_type, *data in htm.htm_parse(strings):
            if op_type == "OPEN":
                if is_first_child:
                    src += "}, ["
                is_first_child = True
                src += "html("
                value, tag = data
                src += (exprs[tag] if value else repr(tag)) + ", {"
            elif op_type == "CLOSE":
                if is_first_child:
                    is_first_child = False
                    src += "}, ["
                src += "])"
            elif op_type == "SPREAD":
                value, item = data
                src += "**" + (exprs[item] if value else item) + ", "
            elif op_type == "PROP_SINGLE":
                attr, value, item = data
                src += (
                    repr(attr) + ": (" + (exprs[item] if value else repr(item)) + "), "
                )
            elif op_type == "PROP_MULTI":
                attr, items = data
                src += (
                    repr(attr)
                    + ": ("
                    + "+".join(
                        repr(value) if is_text else "str(%s)" % exprs[value]
                        for (is_text, value) in items
                    )
                    + "), "
                )
            elif op_type == "CHILD":
                if is_first_child:
                    is_first_child = False
                    src += "}, ["
                value, item = data
                src += (exprs[item] if value else repr(item)) + ", "
            else:
                raise BaseException("unknown op")
        return src
