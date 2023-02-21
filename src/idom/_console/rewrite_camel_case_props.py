from __future__ import annotations

import ast
import re
import sys
from collections.abc import Sequence
from keyword import kwlist
from pathlib import Path

import click

from idom import html
from idom._console.ast_utils import (
    ChangedNode,
    find_element_constructor_usages,
    rewrite_changed_nodes,
)


CAMEL_CASE_SUB_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
def rewrite_camel_case_props(paths: list[str]) -> None:
    """Rewrite camelCase props to snake_case"""
    if sys.version_info < (3, 9):  # pragma: no cover
        raise RuntimeError("This command requires Python>=3.9")

    for p in map(Path, paths):
        for f in [p] if p.is_file() else p.rglob("*.py"):
            result = generate_rewrite(file=f, source=f.read_text())
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
    changed: list[Sequence[ast.AST]] = []
    for el_info in find_element_constructor_usages(tree):
        if isinstance(el_info.props, ast.Dict):
            did_change = False
            keys: list[ast.Constant] = []
            for k in el_info.props.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    new_prop_name = conv_attr_name(k.value)
                    if new_prop_name != k.value:
                        did_change = True
                        keys.append(ast.Constant(conv_attr_name(k.value)))
                    else:
                        keys.append(k)
                else:
                    keys.append(k)
            if not did_change:
                continue
            el_info.props.keys = keys
        else:
            did_change = False
            keywords: list[ast.keyword] = []
            for kw in el_info.props.keywords:
                new_prop_name = conv_attr_name(kw.arg)
                if new_prop_name != kw.arg:
                    did_change = True
                    keywords.append(
                        ast.keyword(arg=conv_attr_name(kw.arg), value=kw.value)
                    )
                else:
                    keywords.append(kw)
            if not did_change:
                continue
            el_info.props.keywords = keywords

        changed.append(ChangedNode(el_info.call, el_info.parents))
    return changed


def conv_attr_name(name: str) -> str:
    new_name = CAMEL_CASE_SUB_PATTERN.sub("_", name).replace("-", "_").lower()
    return f"{new_name}_" if new_name in kwlist else new_name
