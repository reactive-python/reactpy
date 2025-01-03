from __future__ import annotations

import ast
import re
import sys
from copy import copy
from keyword import kwlist
from pathlib import Path
from typing import Callable

import click

from reactpy._console.ast_utils import (
    ChangedNode,
    find_element_constructor_usages,
    rewrite_changed_nodes,
)

CAMEL_CASE_SUB_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
def rewrite_camel_case_props(paths: list[str]) -> None:
    """Rewrite camelCase props to snake_case"""
    if sys.version_info < (3, 9):  # nocov
        msg = "This command requires Python>=3.9"
        raise RuntimeError(msg)

    for p in map(Path, paths):
        for f in [p] if p.is_file() else p.rglob("*.py"):
            result = generate_rewrite(file=f, source=f.read_text(encoding="utf-8"))
            if result is not None:
                f.write_text(result)


def generate_rewrite(file: Path, source: str) -> str | None:
    tree = ast.parse(source)

    changed = find_nodes_to_change(tree)
    if not changed:
        return None

    new = rewrite_changed_nodes(file, source, tree, changed)
    return new


def find_nodes_to_change(tree: ast.AST) -> list[ChangedNode]:
    changed: list[ChangedNode] = []
    for el_info in find_element_constructor_usages(tree):
        if _rewrite_props(el_info.props, _construct_prop_item):
            changed.append(ChangedNode(el_info.call, el_info.parents))
    return changed


def conv_attr_name(name: str) -> str:
    new_name = CAMEL_CASE_SUB_PATTERN.sub("_", name).lower()
    return f"{new_name}_" if new_name in kwlist else new_name


def _construct_prop_item(key: str, value: ast.expr) -> tuple[str, ast.expr]:
    if key == "style" and isinstance(value, (ast.Dict, ast.Call)):
        new_value = copy(value)
        if _rewrite_props(
            new_value,
            lambda k, v: (
                (k, v)
                # avoid infinite recursion
                if k == "style"
                else _construct_prop_item(k, v)
            ),
        ):
            value = new_value
    else:
        key = conv_attr_name(key)
    return key, value


def _rewrite_props(
    props_node: ast.Dict | ast.Call,
    constructor: Callable[[str, ast.expr], tuple[str, ast.expr]],
) -> bool:
    if isinstance(props_node, ast.Dict):
        did_change = False
        keys: list[ast.expr | None] = []
        values: list[ast.expr] = []
        for k, v in zip(props_node.keys, props_node.values):
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                k_value, new_v = constructor(k.value, v)
                if k_value != k.value or new_v is not v:
                    did_change = True
                k = ast.Constant(value=k_value)
                v = new_v
            keys.append(k)
            values.append(v)
        if not did_change:
            return False
        props_node.keys = keys
        props_node.values = values
    else:
        did_change = False
        keywords: list[ast.keyword] = []
        for kw in props_node.keywords:
            if kw.arg is not None:
                kw_arg, kw_value = constructor(kw.arg, kw.value)
                if kw_arg != kw.arg or kw_value is not kw.value:
                    did_change = True
                kw = ast.keyword(arg=kw_arg, value=kw_value)
            keywords.append(kw)
        if not did_change:
            return False
        props_node.keywords = keywords
    return True
