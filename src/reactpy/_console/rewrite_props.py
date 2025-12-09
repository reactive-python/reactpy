from __future__ import annotations

import ast
from collections.abc import Callable
from copy import copy
from keyword import kwlist
from pathlib import Path

import click

from reactpy._console.ast_utils import (
    ChangedNode,
    find_element_constructor_usages,
    rewrite_changed_nodes,
)


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
def rewrite_props(paths: list[str]) -> None:
    """Rewrite snake_case props to camelCase within <PATHS>."""
    for p in map(Path, paths):
        # Process each file or recursively process each Python file in directories
        for f in [p] if p.is_file() else p.rglob("*.py"):
            result = generate_rewrite(file=f, source=f.read_text(encoding="utf-8"))
            if result is not None:
                f.write_text(result)


def generate_rewrite(file: Path, source: str) -> str | None:
    """Generate the rewritten source code if changes are detected"""
    tree = ast.parse(source)  # Parse the source code into an AST

    changed = find_nodes_to_change(tree)  # Find nodes that need to be changed
    if not changed:
        return None  # Return None if no changes are needed

    new = rewrite_changed_nodes(
        file, source, tree, changed
    )  # Rewrite the changed nodes
    return new


def find_nodes_to_change(tree: ast.AST) -> list[ChangedNode]:
    """Find nodes in the AST that need to be changed"""
    changed: list[ChangedNode] = []
    for el_info in find_element_constructor_usages(tree):
        # Check if the props need to be rewritten
        if _rewrite_props(el_info.props, _construct_prop_item):
            # Add the changed node to the list
            changed.append(ChangedNode(el_info.call, el_info.parents))
    return changed


def conv_attr_name(name: str) -> str:
    """Convert snake_case attribute name to camelCase"""
    # Return early if the value is a Python keyword
    if name in kwlist:
        return name

    # Return early if the value is not snake_case
    if "_" not in name:
        return name

    # Split the string by underscores
    components = name.split("_")

    # Capitalize the first letter of each component except the first one
    # and join them together
    return components[0] + "".join(x.title() for x in components[1:])


def _construct_prop_item(key: str, value: ast.expr) -> tuple[str, ast.expr]:
    """Construct a new prop item with the converted key and possibly modified value"""
    if key == "style" and isinstance(value, (ast.Dict, ast.Call)):
        # Create a copy of the value to avoid modifying the original
        new_value = copy(value)
        if _rewrite_props(
            new_value,
            lambda k, v: (
                (k, v)
                # Avoid infinite recursion
                if k == "style"
                else _construct_prop_item(k, v)
            ),
        ):
            # Update the value if changes were made
            value = new_value
    else:
        # Convert the key to camelCase
        key = conv_attr_name(key)
    return key, value


def _rewrite_props(
    props_node: ast.Dict | ast.Call,
    constructor: Callable[[str, ast.expr], tuple[str, ast.expr]],
) -> bool:
    """Rewrite the props in the given AST node using the provided constructor"""
    did_change = False
    if isinstance(props_node, ast.Dict):
        keys: list[ast.expr | None] = []
        values: list[ast.expr] = []
        # Iterate over the keys and values in the dictionary
        for k, v in zip(props_node.keys, props_node.values, strict=False):
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                # Construct the new key and value
                k_value, new_v = constructor(k.value, v)
                if k_value != k.value or new_v is not v:
                    did_change = True
                k = ast.Constant(value=k_value)
                v = new_v
            keys.append(k)
            values.append(v)
        if not did_change:
            return False  # Return False if no changes were made
        props_node.keys = keys
        props_node.values = values
    else:
        did_change = False
        keywords: list[ast.keyword] = []
        # Iterate over the keywords in the call
        for kw in props_node.keywords:
            if kw.arg is not None:
                # Construct the new keyword argument and value
                kw_arg, kw_value = constructor(kw.arg, kw.value)
                if kw_arg != kw.arg or kw_value is not kw.value:
                    did_change = True
                kw = ast.keyword(arg=kw_arg, value=kw_value)
            keywords.append(kw)
        if not did_change:
            return False  # Return False if no changes were made
        props_node.keywords = keywords
    return True
