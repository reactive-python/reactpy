from __future__ import annotations

import ast
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from textwrap import indent
from tokenize import COMMENT as COMMENT_TOKEN
from tokenize import generate_tokens
from typing import Any

import click

from reactpy import html


def rewrite_changed_nodes(
    file: Path,
    source: str,
    tree: ast.AST,
    changed: list[ChangedNode],
) -> str:
    ast.fix_missing_locations(tree)

    lines = source.split("\n")

    # find closest parent nodes that should be re-written
    nodes_to_unparse: list[ast.AST] = []
    for change in changed:
        node_lineage = [change.node, *change.parents]
        for i in range(len(node_lineage) - 1):
            current_node, next_node = node_lineage[i : i + 2]
            if (
                not hasattr(next_node, "lineno")
                or next_node.lineno < change.node.lineno
                or isinstance(next_node, (ast.ClassDef, ast.FunctionDef))
            ):
                nodes_to_unparse.append(current_node)
                break
        else:  # nocov
            msg = "Failed to change code"
            raise RuntimeError(msg)

    # check if an nodes to rewrite contain each other, pick outermost nodes
    current_outermost_node, *sorted_nodes_to_unparse = sorted(
        nodes_to_unparse, key=lambda n: n.lineno
    )
    outermost_nodes_to_unparse = [current_outermost_node]
    for node in sorted_nodes_to_unparse:
        if (
            not current_outermost_node.end_lineno
            or node.lineno > current_outermost_node.end_lineno
        ):
            current_outermost_node = node
            outermost_nodes_to_unparse.append(node)

    moved_comment_lines_from_end: list[int] = []
    # now actually rewrite these nodes (in reverse to avoid changes earlier in file)
    for node in reversed(outermost_nodes_to_unparse):
        # make a best effort to preserve any comments that we're going to overwrite
        comments = _find_comments(lines[node.lineno - 1 : node.end_lineno])

        # there may be some content just before and after the content we're re-writing
        before_replacement = lines[node.lineno - 1][: node.col_offset].lstrip()

        after_replacement = (
            lines[node.end_lineno - 1][node.end_col_offset :].strip()
            if node.end_lineno is not None and node.end_col_offset is not None
            else ""
        )

        replacement = indent(
            before_replacement
            + "\n".join([*comments, ast.unparse(node)])
            + after_replacement,
            " " * (node.col_offset - len(before_replacement)),
        )

        lines[node.lineno - 1 : node.end_lineno or node.lineno] = [replacement]

        if comments:
            moved_comment_lines_from_end.append(len(lines) - node.lineno)

    for lineno_from_end in sorted(set(moved_comment_lines_from_end)):
        click.echo(f"Moved comments to {file}:{len(lines) - lineno_from_end}")

    return "\n".join(lines)


@dataclass
class ChangedNode:
    node: ast.AST
    parents: Sequence[ast.AST]


def find_element_constructor_usages(
    tree: ast.AST, add_props: bool = False
) -> Iterator[ElementConstructorInfo]:
    changed: list[Sequence[ast.AST]] = []
    for parents, node in _walk_with_parent(tree):
        if not (isinstance(node, ast.Call)):
            continue

        func = node.func
        if isinstance(func, ast.Attribute) and (
            (isinstance(func.value, ast.Name) and func.value.id == "html")
            or (isinstance(func.value, ast.Attribute) and func.value.attr == "html")
        ):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id
        else:
            continue

        maybe_attr_dict_node: Any | None = None

        if name == "vdom":
            if len(node.args) == 0:
                continue
            elif len(node.args) == 1:
                maybe_attr_dict_node = ast.Dict(keys=[], values=[])
                if add_props:
                    node.args.append(maybe_attr_dict_node)
                else:
                    continue
            elif isinstance(node.args[1], (ast.Constant, ast.JoinedStr)):
                maybe_attr_dict_node = ast.Dict(keys=[], values=[])
                if add_props:
                    node.args.insert(1, maybe_attr_dict_node)
                else:
                    continue
            elif len(node.args) >= 2:  # noqa: PLR2004
                maybe_attr_dict_node = node.args[1]
        elif hasattr(html, name):
            if len(node.args) == 0:
                maybe_attr_dict_node = ast.Dict(keys=[], values=[])
                if add_props:
                    node.args.append(maybe_attr_dict_node)
                else:
                    continue
            elif isinstance(node.args[0], (ast.Constant, ast.JoinedStr)):
                maybe_attr_dict_node = ast.Dict(keys=[], values=[])
                if add_props:
                    node.args.insert(0, maybe_attr_dict_node)
                else:
                    continue
            else:
                maybe_attr_dict_node = node.args[0]

        if not maybe_attr_dict_node:
            continue

        if isinstance(maybe_attr_dict_node, ast.Dict) or (
            isinstance(maybe_attr_dict_node, ast.Call)
            and isinstance(maybe_attr_dict_node.func, ast.Name)
            and maybe_attr_dict_node.func.id == "dict"
            and isinstance(maybe_attr_dict_node.func.ctx, ast.Load)
        ):
            yield ElementConstructorInfo(node, maybe_attr_dict_node, parents)

    return changed


@dataclass
class ElementConstructorInfo:
    call: ast.Call
    props: ast.Dict | ast.Call
    parents: Sequence[ast.AST]


def _find_comments(lines: list[str]) -> list[str]:
    iter_lines = iter(lines)
    return [
        token
        for token_type, token, _, _, _ in generate_tokens(lambda: next(iter_lines))
        if token_type == COMMENT_TOKEN
    ]


def _walk_with_parent(
    node: ast.AST, parents: tuple[ast.AST, ...] = ()
) -> Iterator[tuple[tuple[ast.AST, ...], ast.AST]]:
    parents = (node, *parents)
    for child in ast.iter_child_nodes(node):
        yield parents, child
        yield from _walk_with_parent(child, parents)
