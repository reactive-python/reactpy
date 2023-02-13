from __future__ import annotations

import ast
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from textwrap import indent
from tokenize import COMMENT as COMMENT_TOKEN
from tokenize import generate_tokens
from typing import Any, Iterator

import click

from idom import html


CAMEL_CASE_SUB_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
def rewrite_keys(paths: list[str]) -> None:
    """Rewrite files under the given paths using the new html element API.

    The old API required users to pass a dictionary of attributes to html element
    constructor functions. For example:

    >>> html.div({"className": "x"}, "y")
    {"tagName": "div", "attributes": {"className": "x"}, "children": ["y"]}

    The latest API though allows for attributes to be passed as snake_cased keyword
    arguments instead. The above example would be rewritten as:

    >>> html.div("y", class_name="x")
    {"tagName": "div", "attributes": {"class_name": "x"}, "children": ["y"]}

    All snake_case attributes are converted to camelCase by the client where necessary.

    ----- Notes -----

    While this command does it's best to preserve as much of the original code as
    possible, there are inevitably some limitations in doing this. As a result, we
    recommend running your code formatter like Black against your code after executing
    this command.

    Additionally, We are unable to perserve the location of comments that lie within any
    rewritten code. This command will place the comments in the code it plans to rewrite
    just above its changes. As such it requires manual intervention to put those
    comments back in their original location.
    """
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
        log_could_not_rewrite(file, tree)
        return None

    new = rewrite_changed_nodes(file, source, tree, changed)
    log_could_not_rewrite(file, ast.parse(new))

    return new


def find_nodes_to_change(tree: ast.AST) -> list[Sequence[ast.AST]]:
    changed: list[Sequence[ast.AST]] = []
    for parents, node in walk_with_parent(tree):
        if not (isinstance(node, ast.Call) and node.keywords):
            continue

        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "html"
        ):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id
        else:
            continue

        for kw in list(node.keywords):
            if kw.arg == "key":
                break
        else:
            continue

        maybe_attr_dict_node: Any | None = None
        if name == "vdom":
            if len(node.args) == 1:
                # vdom("tag") need to add attr dict
                maybe_attr_dict_node = ast.Dict(keys=[], values=[])
                node.args.append(maybe_attr_dict_node)
            elif isinstance(node.args[1], (ast.Constant, ast.JoinedStr)):
                maybe_attr_dict_node = ast.Dict(keys=[], values=[])
                node.args.insert(1, maybe_attr_dict_node)
            elif len(node.args) >= 2:
                maybe_attr_dict_node = node.args[1]
        elif hasattr(html, name):
            if len(node.args) == 0:
                # vdom("tag") need to add attr dict
                maybe_attr_dict_node = ast.Dict(keys=[], values=[])
                node.args.append(maybe_attr_dict_node)
            elif isinstance(node.args[0], (ast.Constant, ast.JoinedStr)):
                maybe_attr_dict_node = ast.Dict(keys=[], values=[])
                node.args.insert(0, maybe_attr_dict_node)
            else:
                maybe_attr_dict_node = node.args[0]

        if not maybe_attr_dict_node:
            continue

        if isinstance(maybe_attr_dict_node, ast.Dict):
            maybe_attr_dict_node.keys.append(ast.Constant("key"))
            maybe_attr_dict_node.values.append(kw.value)
        elif (
            isinstance(maybe_attr_dict_node, ast.Call)
            and isinstance(maybe_attr_dict_node.func, ast.Name)
            and maybe_attr_dict_node.func.id == "dict"
            and isinstance(maybe_attr_dict_node.func.ctx, ast.Load)
        ):
            maybe_attr_dict_node.keywords.append(ast.keyword(arg="key", value=kw.value))
        else:
            continue

        node.keywords.remove(kw)
        changed.append((node, *parents))

    return changed


def rewrite_changed_nodes(
    file: Path,
    source: str,
    tree: ast.AST,
    changed: list[Sequence[ast.AST]],
) -> str:
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
        else:  # pragma: no cover
            raise RuntimeError("Failed to change code")

    # check if an nodes to rewrite contain eachother, pick outermost nodes
    current_outermost_node, *sorted_nodes_to_unparse = list(
        sorted(nodes_to_unparse, key=lambda n: n.lineno)
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
        comments = find_comments(lines[node.lineno - 1 : node.end_lineno])

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

    for lineno_from_end in sorted(list(set(moved_comment_lines_from_end))):
        click.echo(f"Moved comments to {file}:{len(lines) - lineno_from_end}")

    return "\n".join(lines)


def log_could_not_rewrite(file: Path, tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and node.keywords):
            continue

        func = node.func
        if isinstance(func, ast.Attribute):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id
        else:
            continue

        if (
            name == "vdom"
            or hasattr(html, name)
            and any(kw.arg == "key" for kw in node.keywords)
        ):
            click.echo(f"Unable to rewrite usage at {file}:{node.lineno}")


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


@dataclass
class KeywordInfo:
    replace: bool
    keywords: list[ast.keyword]
