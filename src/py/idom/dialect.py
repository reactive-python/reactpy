import ast
from typing import Optional, List, Union, Any, Tuple

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
                if (
                    not node.keywords
                    and len(node.args) == 1
                    and isinstance(node.args[0], ast.JoinedStr)
                ):
                    try:
                        new_node = self._transform_string(node.args[0])
                    except htm.ParseError as error:
                        raise DialectError(str(error), self.filename, node.lineno)
                    return self.generic_visit(
                        ast.fix_missing_locations(ast.copy_location(new_node, node))
                    )
        return node

    def _transform_string(self, node: ast.JoinedStr) -> ast.Call:
        htm_strings: List[str] = []
        exp_nodes: List[ast.AST] = []
        for inner_node in node.values:
            if isinstance(inner_node, ast.Str):
                htm_strings.append(inner_node.s)
            elif isinstance(inner_node, ast.FormattedValue):
                if len(htm_strings) == len(exp_nodes):
                    htm_strings.append("")
                if inner_node.conversion != -1 or inner_node.format_spec:
                    exp_nodes.append(ast.JoinedStr([inner_node]))
                else:
                    exp_nodes.append(inner_node.value)

        call_stack = _HtmlCallStack()
        for op_type, *data in htm.htm_parse(htm_strings):
            getattr(self, f"_transform_htm_{op_type.lower()}")(
                exp_nodes, call_stack, *data
            )
        return call_stack.finish()

    def _transform_htm_open(
        self,
        exp_nodes: List[ast.AST],
        call_stack: "_HtmlCallStack",
        is_index: bool,
        tag_or_index: Union[str, int],
    ) -> None:
        if isinstance(tag_or_index, int):
            call_stack.begin_child(exp_nodes[tag_or_index])
        else:
            call_stack.begin_child(ast.Str(tag_or_index))

    def _transform_htm_close(
        self, exp_nodes: List[ast.AST], call_stack: "_HtmlCallStack"
    ) -> None:
        call_stack.end_child()

    def _transform_htm_spread(
        self, exp_nodes: List[ast.AST], call_stack: "_HtmlCallStack", _: Any, index: int
    ) -> None:
        call_stack.add_attributes(None, exp_nodes[index])

    def _transform_htm_prop_single(
        self,
        exp_nodes: List[ast.AST],
        call_stack: "_HtmlCallStack",
        attr: str,
        is_index: bool,
        value_or_index: Union[str, int],
    ) -> None:
        if isinstance(value_or_index, bool):
            const = ast.NameConstant(value_or_index)
            call_stack.add_attributes(ast.Str(attr), const)
        elif isinstance(value_or_index, int):
            call_stack.add_attributes(ast.Str(attr), exp_nodes[value_or_index])
        else:
            call_stack.add_attributes(ast.Str(attr), ast.Str(value_or_index))

    def _transform_htm_prop_multi(
        self,
        exp_nodes: List[ast.AST],
        call_stack: "_HtmlCallStack",
        attr: str,
        items: Tuple[Tuple[bool, Union[str, int]]],
    ) -> None:
        op_root = current_op = ast.BinOp(None, None, None)
        for _, value_or_index in items:
            if isinstance(value_or_index, str):
                current_op.right = ast.BinOp(ast.Str(value_or_index), ast.Add(), None)
            else:
                current_op.right = ast.BinOp(exp_nodes[value_or_index], ast.Add(), None)
            last_op = current_op
            current_op = current_op.right
        last_op.right = current_op.left
        call_stack.add_attributes(ast.Str(attr), op_root.right)

    def _transform_htm_child(
        self,
        exp_nodes: List[ast.AST],
        call_stack: "_HtmlCallStack",
        is_index: bool,
        child_or_index: Union[str, int],
    ) -> None:
        if isinstance(child_or_index, int):
            call_stack.add_child(exp_nodes[child_or_index])
        else:
            call_stack.add_child(ast.Str(child_or_index))


class _HtmlCallStack:
    def __init__(self) -> None:
        self._root = self._new(ast.Str())
        self._stack: List[ast.Call] = [self._root]

    def begin_child(self, tag: ast.AST) -> None:
        new = self._new(tag)
        last = self._stack[-1]
        children = last.args[2].elts  # type: ignore
        children.append(new)
        self._stack.append(new)

    def add_child(self, child: ast.AST) -> None:
        current = self._stack[-1]
        children = current.args[2].elts  # type: ignore
        children.append(child)

    def add_attributes(self, key: Optional[ast.Str], value: ast.AST) -> None:
        current = self._stack[-1]
        attributes: ast.Dict = current.args[1]  # type: ignore
        attributes.keys.append(key)
        attributes.values.append(value)  # type: ignore

    def end_child(self) -> None:
        self._stack.pop(-1)

    def finish(self) -> ast.Call:
        root = self._root
        self._root = self._new(ast.Str())
        self._stack.clear()
        return root.args[2].elts[0]  # type: ignore

    @staticmethod
    def _new(tag: ast.AST) -> ast.Call:
        args = [tag, ast.Dict([], []), ast.List([], ast.Load())]
        return ast.Call(ast.Name("html", ast.Load()), args, [])
