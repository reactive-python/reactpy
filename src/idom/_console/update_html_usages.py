from __future__ import annotations

import ast
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from keyword import kwlist
from pathlib import Path
from textwrap import indent
from tokenize import COMMENT as COMMENT_TOKEN
from tokenize import generate_tokens
from typing import Iterator

import click

from idom import html


CAMEL_CASE_SUB_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
def update_html_usages(paths: list[str]) -> None:
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

    changed: list[Sequence[ast.AST]] = []
    for parents, node in walk_with_parent(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func
        if isinstance(func, ast.Attribute):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id
        else:
            continue

        if name == "vdom":
            if len(node.args) < 2:
                continue
            maybe_attr_dict_node = node.args[1]
            # remove attr dict from new args
            new_args = node.args[:1] + node.args[2:]
        elif hasattr(html, name):
            if len(node.args) == 0:
                continue
            maybe_attr_dict_node = node.args[0]
            # remove attr dict from new args
            new_args = node.args[1:]
        else:
            continue

        new_keyword_info = extract_keywords(maybe_attr_dict_node)
        if new_keyword_info is not None:
            if new_keyword_info.replace:
                node.keywords = new_keyword_info.keywords
            else:
                node.keywords.extend(new_keyword_info.keywords)

            node.args = new_args
            changed.append((node, *parents))

    if not changed:
        return None

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


def extract_keywords(node: ast.AST) -> KeywordInfo | None:
    if isinstance(node, ast.Dict):
        keywords: list[ast.keyword] = []
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                if k.value == "tagName":
                    # this is a vdom dict declaration
                    return None
                keywords.append(ast.keyword(arg=conv_attr_name(k.value), value=v))
            else:
                return KeywordInfo(
                    replace=True,
                    keywords=[ast.keyword(arg=None, value=node)],
                )
        return KeywordInfo(replace=False, keywords=keywords)
    elif (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "dict"
        and isinstance(node.func.ctx, ast.Load)
    ):
        keywords = [ast.keyword(arg=None, value=a) for a in node.args]
        for kw in node.keywords:
            if kw.arg == "tagName":
                # this is a vdom dict declaration
                return None
            if kw.arg is not None:
                keywords.append(ast.keyword(arg=conv_attr_name(kw.arg), value=kw.value))
            else:
                keywords.append(kw)
        return KeywordInfo(replace=False, keywords=keywords)
    return None


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


@dataclass
class KeywordInfo:
    replace: bool
    keywords: list[ast.keyword]
