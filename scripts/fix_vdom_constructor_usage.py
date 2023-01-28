from __future__ import annotations

import ast
import re
import sys
from collections.abc import Sequence
from keyword import kwlist
from pathlib import Path
from textwrap import dedent, indent
from tokenize import COMMENT as COMMENT_TOKEN
from tokenize import generate_tokens
from typing import Iterator

from idom import html


CAMEL_CASE_SUB_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")
TEST_OUTPUT_TEMPLATE = """

{actual}

▲   actual   ▲
▼  expected  ▼

{expected}

"""


def update_vdom_constructor_usages(source: str, filename: str = "") -> None:
    tree = ast.parse(source)

    changed: list[Sequence[ast.AST]] = []
    for parents, node in walk_with_parent(tree):
        if isinstance(node, ast.Call):
            func = node.func
            match func:
                case ast.Attribute():
                    name = func.attr
                case ast.Name(ctx=ast.Load()):
                    name = func.id
                case _:
                    name = ""
            if hasattr(html, name):
                match node.args:
                    case [ast.Dict(keys, values), *_]:
                        new_kwargs = list(node.keywords)
                        for k, v in zip(keys, values):
                            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                                new_kwargs.append(
                                    ast.keyword(arg=conv_attr_name(k.value), value=v)
                                )
                            else:
                                new_kwargs = [ast.keyword(arg=None, value=node.args[0])]
                                break
                        node.args = node.args[1:]
                        node.keywords = new_kwargs
                        changed.append((node, *parents))
                    case [
                        ast.Call(
                            func=ast.Name(id="dict", ctx=ast.Load()),
                            args=args,
                            keywords=kwargs,
                        ),
                        *_,
                    ]:
                        new_kwargs = [
                            *[ast.keyword(arg=None, value=a) for a in args],
                            *node.keywords,
                        ]
                        for kw in kwargs:
                            if kw.arg is not None:
                                new_kwargs.append(
                                    ast.keyword(
                                        arg=conv_attr_name(kw.arg), value=kw.value
                                    )
                                )
                            else:
                                new_kwargs.append(kw)
                        node.args = node.args[1:]
                        node.keywords = new_kwargs
                        changed.append((node, *parents))

                    case _:
                        pass

    if not changed:
        return

    ast.fix_missing_locations(tree)

    lines = source.split("\n")

    # find closest parent nodes that should be re-written
    nodes_to_unparse: list[ast.AST] = []
    for node_lineage in changed:
        origin_node = node_lineage[0]
        for i in range(len(node_lineage) - 1):
            current_node, next_node = node_lineage[i : i + 2]
            if (
                not hasattr(next_node, "lineno")
                or next_node.lineno < origin_node.lineno
                or isinstance(next_node, (ast.ClassDef, ast.FunctionDef))
            ):
                nodes_to_unparse.append(current_node)
                break
        else:
            raise RuntimeError("Failed to change code")

    # check if an nodes to rewrite contain eachother, pick outermost nodes
    current_outermost_node, *sorted_nodes_to_unparse = list(
        sorted(nodes_to_unparse, key=lambda n: n.lineno)
    )
    outermost_nodes_to_unparse = [current_outermost_node]
    for node in sorted_nodes_to_unparse:
        if node.lineno > current_outermost_node.end_lineno:
            current_outermost_node = node
            outermost_nodes_to_unparse.append(node)

    moved_comment_lines_from_end: list[int] = []
    # now actually rewrite these nodes (in reverse to avoid changes earlier in file)
    for node in reversed(outermost_nodes_to_unparse):
        # make a best effort to preserve any comments that we're going to overwrite
        comments = find_comments(lines[node.lineno - 1 : node.end_lineno])

        # there may be some content just before and after the content we're re-writing
        before_replacement = lines[node.lineno - 1][: node.col_offset].lstrip()

        if node.end_lineno is not None and node.end_col_offset is not None:
            after_replacement = lines[node.end_lineno - 1][
                node.end_col_offset :
            ].strip()
        else:
            after_replacement = ""

        replacement = indent(
            before_replacement
            + "\n".join([*comments, ast.unparse(node)])
            + after_replacement,
            " " * (node.col_offset - len(before_replacement)),
        )

        if node.end_lineno:
            lines[node.lineno - 1 : node.end_lineno] = [replacement]
        else:
            lines[node.lineno - 1] = replacement

        if comments:
            moved_comment_lines_from_end.append(len(lines) - node.lineno)

    for lineno_from_end in sorted(list(set(moved_comment_lines_from_end))):
        print(f"Moved comments to {filename}:{len(lines) - lineno_from_end}")

    return "\n".join(lines)


def find_comments(lines: list[str]) -> list[str]:
    iter_lines = iter(lines)
    return [
        token
        for token_type, token, _, _, _ in generate_tokens(lambda: next(iter_lines))
        if token_type == COMMENT_TOKEN
    ]


def walk_with_parent(
    node: ast.AST, parents: tuple[ast.AST, ...] = ()
) -> Iterator[tuple[tuple[ast.AST, ...], ast.AST]]:
    parents = (node,) + parents
    for child in ast.iter_child_nodes(node):
        yield parents, child
        yield from walk_with_parent(child, parents)


def conv_attr_name(name: str) -> str:
    new_name = CAMEL_CASE_SUB_PATTERN.sub("_", name).replace("-", "_").lower()
    return f"{new_name}_" if new_name in kwlist else new_name


def run_tests():
    cases = [
        # simple conversions
        (
            'html.div({"className": "test"})',
            "html.div(class_name='test')",
        ),
        (
            'html.div({class_name: "test", **other})',
            "html.div(**{class_name: 'test', **other})",
        ),
        (
            'html.div(dict(other, className="test"))',
            "html.div(**other, class_name='test')",
        ),
        (
            'html.div({"className": "outer"}, html.div({"className": "inner"}))',
            "html.div(html.div(class_name='inner'), class_name='outer')",
        ),
        (
            'html.div({"className": "outer"}, html.div({"className": "inner"}))',
            "html.div(html.div(class_name='inner'), class_name='outer')",
        ),
        (
            '["before", html.div({"className": "test"}), "after"]',
            "['before', html.div(class_name='test'), 'after']",
        ),
        (
            """
            html.div(
                {"className": "outer"},
                html.div({"className": "inner"}),
                html.div({"className": "inner"}),
            )
            """,
            "html.div(html.div(class_name='inner'), html.div(class_name='inner'), class_name='outer')",
        ),
        (
            'html.div(dict(className="test"))',
            "html.div(class_name='test')",
        ),
        # when to not attempt conversion
        (
            'html.div(ignore, {"className": "test"})',
            None,
        ),
        # avoid unnecessary changes
        (
            """
            def my_function():
                x = 1  # some comment
                return html.div({"className": "test"})
            """,
            """
            def my_function():
                x = 1  # some comment
                return html.div(class_name='test')
            """,
        ),
        (
            """
            if condition:
                # some comment
                dom = html.div({"className": "test"})
            """,
            """
            if condition:
                # some comment
                dom = html.div(class_name='test')
            """,
        ),
        (
            """
            [
                html.div({"className": "test"}),
                html.div({"className": "test"}),
            ]
            """,
            """
            [
                html.div(class_name='test'),
                html.div(class_name='test'),
            ]
            """,
        ),
        (
            """
            @deco(
                html.div({"className": "test"}),
                html.div({"className": "test"}),
            )
            def func():
                # comment
                x = [
                    1
                ]
            """,
            """
            @deco(
                html.div(class_name='test'),
                html.div(class_name='test'),
            )
            def func():
                # comment
                x = [
                    1
                ]
            """,
        ),
        (
            """
            @deco(html.div({"className": "test"}), html.div({"className": "test"}))
            def func():
                # comment
                x = [
                    1
                ]
            """,
            """
            @deco(html.div(class_name='test'), html.div(class_name='test'))
            def func():
                # comment
                x = [
                    1
                ]
            """,
        ),
        (
            """
            (
                result
                if condition
                else html.div({"className": "test"})
            )
            """,
            """
            (
                result
                if condition
                else html.div(class_name='test')
            )
            """,
        ),
        # best effort to preserve comments
        (
            """
            x = 1
            html.div(
                # comment 1
                {"className": "outer"},
                # comment 2
                html.div({"className": "inner"}),
            )
            """,
            """
            x = 1
            # comment 1
            # comment 2
            html.div(html.div(class_name='inner'), class_name='outer')
            """,
        ),
    ]

    for source, expected in cases:
        actual = update_vdom_constructor_usages(dedent(source).strip(), "test.py")
        if isinstance(expected, str):
            expected = dedent(expected).strip()
        if actual != expected:
            print(TEST_OUTPUT_TEMPLATE.format(actual=actual, expected=expected))
            return False

    return True


if __name__ == "__main__":
    argv = sys.argv[1:]

    if not argv:
        print("Running tests...")
        result = run_tests()
        print("Success" if result else "Failed")
        sys.exit(0 if result else 0)

    for pattern in argv:
        for file in Path.cwd().glob(pattern):
            result = update_vdom_constructor_usages(
                source=file.read_text(),
                filename=str(file),
            )
            if result is not None:
                file.write_text(result)
