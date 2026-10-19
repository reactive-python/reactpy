"""MkDocs hook: make the ``:material-play: Run`` tab placeholders execute for real.

Loaded by MkDocs' builtin ``hooks:`` config, so there is no entry point to
install, no ``PYTHONPATH`` to set, and no new dependency:

    # docs/mkdocs.yml
    hooks:
        - plugins/reactpy_run.py

Which files a Run tab executes is **inferred from the sibling tabs** of the
same tab set, because their ``{% include "../../examples/<demo>/…" %}``
directives already name them. A Run tab therefore cannot drift from the code
it runs, and authoring a new one costs nothing.

Authoring (unchanged from today)::

    === "app.py"

        ```python
        {% include "../../examples/rendering_lists/from_array/app.py" start="# start" %}
        ```

    === ":material-play: Run"

        ```python
        # TODO
        ```

Rare cases get an explicit fence inside the Run tab instead::

    === ":material-play: Run"

        ```reactpy-run
        dir: reference_reactpy_csr
        files: csr/main.py csr_root/root.py
        root: my_app
        ```

Rendering reuses ReactPyCsr's own primitives: ``pyscript_setup_html`` /
``pyscript_executor_html``. One Pyodide interpreter is shared per page and is
**not loaded until the first Run click**, so a docs page with 8 demos costs
exactly what a docs page with 0 demos costs.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import textwrap
from collections.abc import Iterator
from pathlib import Path
from typing import Any, TypedDict

from mkdocs.plugins import event_priority

# ------------------------------------------------------------------ tuning --

TAB_TITLE = ":material-play: Run"
EXAMPLES_DIR_NAME = "examples"
RUNTIME_DIR = "assets/reactpy-runtime"
STATIC_IGNORES = ("*.map", "index*.js", "preact*")

# ReactPy hands PyScript root-absolute asset URLs (``/reactpy/static/…``),
# which only work when ReactPy itself serves the page. The generated config
# replaces that prefix with this marker and the client expands it.
STATIC_MARKER = "__REACTPY_STATIC__"
_ROOT_NAME_PREFERENCE = ("my_app", "app", "main", "root")
_MODULE_GLOBALS_RE = re.compile(
    r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*) *(?:\+|-|\*|/|%|\*\*)?=(?!=)", re.M
)

# Run *before* mkdocs-include-markdown-plugin (priority 100) so that the
# ``{% include %}`` directives we infer from are still in the markdown.
_INFERENCE_PRIORITY = 200

_INCLUDE_RE = re.compile(r'\{%\s*include\s+"(?P<path>[^"]+?)"[^%]*%\}')
_IMPORT_RE = re.compile(r"^(?:from|import)\s+([A-Za-z_][\w.]*)", re.MULTILINE)
_TAB_RE = re.compile(r'^[ \t]*=== "(?P<title>[^"]*)"[ \t]*$', re.MULTILINE)
_FENCE_RE = re.compile(r"^[ \t]*(?:```|~~~)", re.MULTILINE)
_COMPONENT_RE = re.compile(r"@component\s*\n(?:@[^\n]*\n)*[ \t]*def (?P<name>\w+)\(")
_ROOT_MARKER_RE = re.compile(r"^[ \t]*#[ \t]*root:[ \t]*(?P<name>\w+)", re.MULTILINE)
_OVERRIDES_RE = re.compile(
    r"^([ \t]*)```reactpy-run[ \t]*\n(.*?)\1```[ \t]*$", re.MULTILINE | re.DOTALL
)


# ------------------------------------------------------------------- state --


class _Resolved(TypedDict):
    """The files a Run tab executes, and the directory label to show."""

    main: Path
    extra: list[Path]
    css: list[Path]
    parts: list[str]


class _State:
    def __init__(self) -> None:
        self.blocks: dict[str, list[dict[str, Any]]] = {}
        self.examples_dir: Path = Path("docs/examples")
        self.site_dir: Path | None = None


_state = _State()


# ----------------------------------------------------------------- events --


def on_config(config):
    docs_dir = Path(config["docs_dir"])
    _state.examples_dir = (docs_dir.parent / EXAMPLES_DIR_NAME).resolve()
    return config


def on_post_build(config):
    """Copy ReactPy's vendored PyScript runtime into the site, once per build."""
    import reactpy

    site_dir = Path(config["site_dir"])
    static_src = Path(reactpy.__file__).parent / "static"
    static_dst = site_dir / RUNTIME_DIR / "static"
    if static_dst.exists():
        shutil.rmtree(static_dst)
    shutil.copytree(
        static_src, static_dst, ignore=shutil.ignore_patterns(*STATIC_IGNORES)
    )
    _write_runtime_config(site_dir, config)


@event_priority(_INFERENCE_PRIORITY)
def on_page_markdown(markdown, page, config, files):
    blocks: list[dict[str, Any]] = []
    edits: list[tuple[int, int, str]] = []

    for index, (tab_set, tab) in enumerate(_run_tabs(markdown)):
        block = _build_block(markdown, tab, tab_set, page, index)
        blocks.append(block)
        indent = " " * (len(tab["indent"]) + 4)
        body = f"{indent}<!--REACTPY-RUN:{block['id']}-->\n\n"
        edits.append((tab["body_start"], tab["body_end"], body))

    _state.blocks[page.file.src_path] = blocks
    # Apply from the back so earlier offsets stay valid.
    for start, end, body in sorted(edits, key=lambda e: e[0], reverse=True):
        markdown = markdown[:start] + body + markdown[end:]
    return markdown


def on_page_content(html, page, config, files):
    blocks = _state.blocks.get(page.file.src_path) or []
    if not blocks:
        return html

    base = _relative_to_page(page)
    templates: list[str] = []
    for block in blocks:
        marker = f"<!--REACTPY-RUN:{block['id']}-->"
        if block.get("error"):
            html = html.replace(
                marker,
                '<div class="reactpy-run reactpy-run--error">'
                f'<span class="reactpy-run-msg">{block["label"]}: {block["error"]}</span></div>',
            )
            continue
        html = html.replace(
            marker,
            # No title, no button: opening the Run tab is itself the signal to
            # execute, and the panel is styled to read as one of the page's
            # code blocks.
            f'<div class="reactpy-run" data-reactpy-run="{block["id"]}">'
            # The id/class/``data-uuid`` trio is ReactPyCsr's contract: the
            # layout handler renders into ``#pyscript-<uuid>`` and reclaims
            # workspaces by reading ``.pyscript`` elements' ``data-uuid``.
            f'<div class="reactpy-run-out pyscript" id="pyscript-{block["uuid"]}" '
            f'data-uuid="{block["uuid"]}"></div>'
            '<div class="reactpy-run-status" hidden></div></div>',
        )
        templates.append(
            f'<template id="reactpy-src-{block["id"]}">'
            f"{block['css_html']}"
            f'<script type="py">{block["executor"]}</script></template>'
        )

    return (
        html
        + f'<link rel="stylesheet" href="{base}assets/css/reactpy-run.css" />'
        + f'<script type="module" src="{base}assets/js/reactpy-run.js"></script>'
        + "".join(templates)
    )


def _relative_to_page(page) -> str:
    """MkDocs rewrites links in markdown, but not the raw HTML we inject.

    ``page.file.dest_uri`` is the page's path under ``site/``, so its depth is
    exactly how many ``../`` the injected URLs need. This keeps the runtime
    working under mike's versioned URLs (``/reactpy/dev/learn/…``) and with
    ``use_directory_urls: false``.
    """
    from posixpath import dirname

    directory = dirname(page.file.dest_uri)
    return "" if directory in ("", ".") else "../" * (directory.count("/") + 1)


# -------------------------------------------------------------- generation --


def _run_tabs(markdown: str) -> Iterator[tuple[dict, dict]]:
    """Every ``:material-play: Run`` tab, with the tab set that contains it."""
    for tab_set in _tab_sets(markdown):
        for tab in tab_set["tabs"]:
            if tab["title"].strip() != TAB_TITLE:
                continue
            if _inside_code_fence(markdown, tab["start"]):
                # A page documenting the Run convention is not a demo.
                continue
            yield tab_set, tab


def _inside_code_fence(markdown: str, pos: int) -> bool:
    """Whether *pos* sits inside a fenced code block."""
    return len(_FENCE_RE.findall(markdown[:pos])) % 2 == 1


def _build_block(
    markdown: str,
    tab: dict[str, Any],
    tab_set: dict[str, Any],
    page: Any,
    index: int,
) -> dict[str, Any]:
    from uuid import uuid4

    from reactpy.executors.pyscript.utils import pyscript_executor_html

    body = markdown[tab["body_start"] : tab["body_end"]]
    overrides = _parse_overrides(body)
    resolved, error = _resolve_files(markdown, tab, tab_set, page, overrides)
    label = overrides.get("dir") or ("/".join(resolved["parts"]) if resolved else "?")
    # Content alone is not unique: two demos on one page can share a
    # directory, and they must not collide with each other's DOM ids.
    block_id = _make_id(page.file.src_path, str(index), label or "")

    if resolved is None or error:
        return {
            "id": block_id,
            "label": label,
            "error": error or "Nothing runnable was found in the sibling tabs",
        }

    main_file = resolved["main"]
    extra_files = resolved["extra"]
    merged = _merged_source([main_file, *extra_files])
    cache = {str(main_file): merged}
    uuid = uuid4().hex

    root = overrides.get("root") or _guess_root(main_file)
    if root is None:
        # Script-style examples (they ``print()`` VDOM rather than mount a
        # component) still get a Run tab: their stdout becomes a <pre>.
        root, cache[str(main_file)] = "_console_output", _as_console_script(merged)
    elif f"def {root}():" not in merged:
        # The example's outermost component takes props, and ReactPy's
        # executor only mounts zero-argument ones. Mount it from a wrapper,
        # passing whatever the page declared (``props: symbol="BTC"``).
        args = overrides.get("props", "")
        if not args and _requires_props(merged, root):
            return {
                "id": block_id,
                "label": label,
                "error": f"{root}() needs props; add a props: line to the fence",
            }
        cache[str(main_file)] = merged + _mount_wrapper(root, args)
        root = "_reactpy_run_root"

    if syntax_error := _nested_syntax_error(cache[str(main_file)]):
        return {"id": block_id, "label": label, "error": syntax_error}

    try:
        executor = pyscript_executor_html(
            file_paths=[str(main_file)],
            uuid=uuid,
            root=root,
            cache_handler=lambda path, **_: cache[path],
        )
    except Exception as exc:
        return {"id": block_id, "label": label, "error": str(exc)}

    css_html = ""
    for css_file in resolved["css"]:
        scoped = _scope_css(css_file.read_text(encoding="utf-8"), f"#pyscript-{uuid}")
        css_html += f"<style>{scoped}</style>"

    return {
        "id": block_id,
        "label": label,
        "uuid": uuid,
        "executor": executor,
        "css_html": css_html,
    }


def _parse_overrides(body: str) -> dict[str, str]:
    """Read the ``key: value`` lines of a ``reactpy-run`` fence, if present.

    Recognised keys are ``dir:`` (which example directory), ``files:`` (which
    files within it), ``root:`` (which component to mount), and ``props:``
    (arguments for a component whose parameters have no defaults).
    """
    match = _OVERRIDES_RE.search(body)
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group(2).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            values[key.strip()] = value.strip()
    return values


def _resolve_files(
    markdown: str,
    tab: dict[str, Any],
    tab_set: dict[str, Any],
    page: Any,
    overrides: dict[str, str],
) -> tuple[_Resolved | None, str | None]:
    """Work out which example files a Run tab should execute.

    Either an author tells us (``dir:``/``files:`` in a ``reactpy-run`` fence)
    or we read it off the sibling tabs' ``{% include %}`` directives, which
    already name these exact files.
    """
    examples = _state.examples_dir
    page_dir = Path(page.file.abs_src_path).parent

    if overrides.get("dir"):
        demo_dir = examples / overrides["dir"]
        if not demo_dir.is_dir():
            return None, f"No such example directory: {overrides['dir']}"
        if overrides.get("files"):
            found = [demo_dir / name.strip() for name in overrides["files"].split(",")]
        else:
            found = sorted(
                p for p in demo_dir.rglob("*.py") if "__pycache__" not in p.parts
            )
            found += sorted(demo_dir.glob("*.css"))
        label = [overrides["dir"]]
    elif overrides.get("files"):
        found, label = [], None
        for name in (n.strip() for n in overrides["files"].split(",")):
            matches = sorted(
                p
                for p in examples.rglob(name)
                if p.is_file() and "__pycache__" not in p.parts
            )
            if len(matches) > 1:
                names = ", ".join(str(m.relative_to(examples)) for m in matches)
                return None, f"'{name}' is ambiguous ({names}); add a dir: line"
            if not matches:
                return None, f"No example file named '{name}'"
            found.append(matches[0])
            label = str(_demo_dir_of(matches[0], examples).relative_to(examples))
        if label is None:
            return None, "files: listed nothing"
        label = [label]
    else:
        found = []
        for sibling in tab_set["tabs"]:
            if sibling is tab:
                continue
            for match in _INCLUDE_RE.finditer(
                markdown[sibling["body_start"] : sibling["body_end"]]
            ):
                candidate = (page_dir / match.group("path")).resolve()
                if candidate.is_file() and _is_under(candidate, examples):
                    found.append(candidate)
        label = None

    if not found:
        return None, "Nothing runnable was found in the sibling tabs"
    if missing := [str(p.relative_to(examples)) for p in found if not p.is_file()]:
        return None, f"No such example file(s): {', '.join(missing)}"

    # A shared file that lives *above* the demo (a page-level ``game.css``) is
    # part of that demo, not a second directory competing to be its root.
    groups: dict[Path, list[Path]] = {}
    for path in found:
        groups.setdefault(_demo_dir_of(path, examples), []).append(path)
    primary = max(
        groups,
        key=lambda d: (
            sum(p.suffix == ".py" for p in groups[d]),
            len(d.relative_to(examples).parts),
        ),
    )
    files = list(groups[primary])
    for directory, members in groups.items():
        if directory == primary:
            continue
        if directory in primary.parents:
            files.extend(members)
        elif label is None:
            names = ", ".join(sorted(str(g.relative_to(examples)) for g in groups))
            return (
                None,
                f"Multiple example directories ({names}); add a reactpy-run fence",
            )

    # A demo may import a sibling the page never shows (``data.py``). Add what
    # the code actually imports, transitively — not every file in the
    # directory, which would drag in the alternative versions of it.
    if label is None:
        files = _with_imported_siblings(files, primary)

    py = [p for p in _order(files) if p.suffix == ".py"]
    css = [p for p in sorted(files) if p.suffix == ".css"]
    if not py:
        return None, f"No Python files for {primary.relative_to(examples)}"
    return {
        "main": py[0],
        "extra": py[1:],
        "css": css,
        "parts": label or list(primary.relative_to(examples).parts),
    }, None


def _demo_dir_of(path: Path, examples: Path) -> Path:
    """``examples/<page_slug>/<demo>/app.py`` -> ``examples/<page_slug>/<demo>``."""
    rel = path.relative_to(examples)
    return examples / rel.parent


def _with_imported_siblings(files: list[Path], directory: Path) -> list[Path]:
    """Add sibling modules that *files* import, directly or transitively.

    A demo's helper module (``data.py``, ``tasks.py``) is part of the demo even
    when the page only shows ``app.py``. The reverse would be wrong: a
    directory often holds *alternative* versions of a demo, and merging those
    in produces a module that imports a web server.
    """
    included = list(files)
    queue = list(files)
    while queue:
        source = queue.pop().read_text(encoding="utf-8")
        for name in {m.split(".")[0] for m in _IMPORT_RE.findall(source)}:
            for module in sorted(directory.glob(f"{name}.py")):
                if module not in included:
                    included.append(module)
                    queue.append(module)
    return included


def _order(files: list[Path]) -> list[Path]:
    def rank(path: Path) -> tuple[int, str]:
        # app.py is the component; main.py is an ASGI server (never the root).
        return (
            0 if path.name == "app.py" else 1 if path.name != "main.py" else 2,
            path.name,
        )

    return sorted(files, key=rank)


def _merged_source(files: list[Path]) -> str:
    """Concatenate a demo's files, shimming cross-file imports.

    PyScript gets one flat script, so ``from data import people`` would raise
    ``ModuleNotFoundError``. Registering the siblings in ``sys.modules`` from
    embedded strings keeps the on-disk files importable as normal modules.
    """
    # Everything below lands inside one function, so a module-level
    # assignment becomes a local and any ``global`` in the example then reads
    # a name that was never bound. Declare those names global up front.
    declared = _MODULE_GLOBALS_RE.findall(files[0].read_text(encoding="utf-8"))
    head: list[str] = (
        [f"global {', '.join(sorted(set(declared)))}", ""] if declared else []
    ) + ["import sys, types", ""]
    for path in files[1:]:
        name, source = path.stem, path.read_text(encoding="utf-8")
        head += [
            f"_{name}_src = {json.dumps(source)}",
            f"_{name}_mod = types.ModuleType({json.dumps(name)})",
            f"exec(compile(_{name}_src, {json.dumps(name + '.py')}, 'exec'), _{name}_mod.__dict__)",
            f"sys.modules[{json.dumps(name)}] = _{name}_mod",
            f"del _{name}_src, _{name}_mod",
            "",
        ]
    return "\n".join(head) + files[0].read_text(encoding="utf-8")


def _guess_root(main_file: Path) -> str | None:
    """The component nothing else renders — that is what the page mounts.

    Declaring the outermost component last is the common convention, but not a
    rule, so prefer the component no other one calls, and fall back to the
    last declaration when that is ambiguous.
    """
    text = main_file.read_text(encoding="utf-8")
    if marked := _ROOT_MARKER_RE.search(text):
        return marked.group("name")

    names = _COMPONENT_RE.findall(text)
    if not names:
        return None

    roots = [
        name
        for name in names
        if not re.search(rf"\b{name}\(", re.sub(rf"def {name}\(", "(", text))
    ]
    for preferred in _ROOT_NAME_PREFERENCE:
        if preferred in roots:
            return preferred
    return roots[-1] if roots else names[-1]


def _requires_props(source: str, root: str) -> bool:
    """Whether ``root`` has parameters without defaults, so it needs props."""
    match = re.search(rf"def {re.escape(root)}\(([^)]*)\)", source)
    if not match:
        return False
    params = [p.strip() for p in match.group(1).split(",") if p.strip()]
    return any("=" not in p for p in params)


def _nested_syntax_error(script: str) -> str | None:
    """Compile the script the way PyScript runs it — inside a function.

    Top-level Python accepts what a nested scope refuses: a name both annotated
    and declared ``global`` is one such case. In the browser a syntax error is
    a button that does nothing, so catch it where it can still be reported.
    """
    nested = "def _reactpy_run_probe():\n" + textwrap.indent(script, "    ")
    try:
        compile(nested, "<reactpy-run>", "exec")
    except SyntaxError as error:
        return f"{error.msg} (line {error.lineno})"
    return None


def _mount_wrapper(root: str, args: str = "") -> str:
    """Mount an example's component from a zero-argument root.

    ``pyscript_executor_html`` refuses to mount anything but ``def name():``,
    and plenty of teaching examples are components that take props.
    """
    return (
        "\n\nimport reactpy as _reactpy_run_rt\n\n\n"
        "@_reactpy_run_rt.component\n"
        "def _reactpy_run_root():\n"
        f"    return {root}({args})\n"
    )


def _as_console_script(source: str) -> str:
    """Turn a print-style example into a component that shows its stdout.

    Roughly a fifth of the examples teach VDOM by ``print()``-ing a result
    rather than mounting a component, so there is no root component to run.
    Capturing stdout and rendering it keeps those examples runnable instead of
    leaving them as dead placeholders.
    """
    import textwrap

    return (
        "import contextlib\nimport io\nfrom reactpy import component, html\n\n"
        "_stdout = io.StringIO()\n"
        "with contextlib.redirect_stdout(_stdout):\n"
        f"{textwrap.indent(source, '    ')}\n\n"
        "@component\n"
        "def _console_output():\n"
        '    return html.pre(_stdout.getvalue() or "(no output)")\n'
    )


# ------------------------------------------------------------------ utils --


def _tab_sets(markdown: str) -> list[dict]:
    """Group consecutive ``=== "Title"`` tabs that form one tab set."""
    tabs = [
        {
            "indent": m.group(0)[: len(m.group(0)) - len(m.group(0).lstrip())],
            "title": m.group("title"),
            "start": m.start(),
            "line_end": m.end() + 1,
        }
        for m in _TAB_RE.finditer(markdown)
    ]
    sets: list[dict] = []
    for tab in tabs:
        if (
            sets
            and sets[-1]["indent"] == tab["indent"]
            and _still_in_set(markdown, sets[-1]["end"], tab["start"], tab["indent"])
        ):
            sets[-1]["tabs"].append(tab)
        else:
            sets.append(
                {"indent": tab["indent"], "tabs": [tab], "end": tab["line_end"]}
            )
        # A set runs to the end of its last tab's indented body block.
        sets[-1]["end"] = _consume_body(markdown, tab["line_end"], tab["indent"])

    for group in sets:
        for i, tab in enumerate(group["tabs"]):
            tab["body_start"] = tab["line_end"]
            tab["body_end"] = (
                group["tabs"][i + 1]["start"]
                if i + 1 < len(group["tabs"])
                else group["end"]
            )
    return sets


def _still_in_set(markdown: str, from_pos: int, to_pos: int, indent: str) -> bool:
    """True if only blank or deeper-indented lines sit between two tabs."""
    for line in markdown[from_pos:to_pos].splitlines():
        if (
            line.strip()
            and not line.startswith(" " * (len(indent) + 1))
            and not line.startswith("\t")
        ):
            return False
    return True


def _consume_body(markdown: str, pos: int, indent: str) -> int:
    """Offset just past the indented block that follows a ``=== "Title"`` line."""
    deeper = " " * (len(indent) + 1)
    end = pos
    for line in markdown[pos:].split("\n"):
        if not line.strip() or line.startswith(deeper) or line.startswith("\t"):
            end += len(line) + 1
        else:
            break
    # Trailing blank lines belong to whatever comes next, not to this body.
    return pos + len(markdown[pos:end].rstrip("\n"))


def _scope_css(css: str, container_selector: str) -> str:
    """Attach a demo's CSS to its own container so docs styles do not leak."""
    out: list[str] = []
    for rule in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        selectors, declarations = rule
        if selectors.strip().startswith("@"):
            continue
        scoped = []
        for selector in selectors.split(","):
            sel = selector.strip()
            if not sel:
                continue
            if sel in {"body", "html", "*"}:
                scoped.append(container_selector)
            else:
                scoped.append(f"{container_selector} {sel}")
        out.append(f"{', '.join(scoped)}{{{declarations}}}")
    return "".join(out)


def _is_under(path: Path, root: Path) -> bool:
    return root in path.parents


def _make_id(*parts: str) -> str:
    return hashlib.md5("\0".join(parts).encode(), usedforsecurity=False).hexdigest()[
        :12
    ]


def _write_runtime_config(site_dir: Path, config) -> None:
    """Emit the PyScript bootstrap constants straight from ReactPy itself."""
    from reactpy.executors.pyscript.utils import (
        PYSCRIPT_LAYOUT_HANDLER,
        extend_pyscript_config,
    )

    # PyScript resolves every URL in this JSON against the *document*, so a
    # relative path would break on a page at /learn/some/page/. Hand it a
    # marker instead and let the client expand it relative to this file. The
    # wheel may be cached because ReactPy names it after its own bytes, so the
    # URL changes whenever the wheel does.
    pyscript_config = extend_pyscript_config(
        [], {}, {}, asset_prefix=STATIC_MARKER, packages_cache="normal"
    )
    payload = {
        "staticRoot": "static",
        "staticMarker": STATIC_MARKER,
        "pyscriptConfig": pyscript_config,
        "layoutHandler": PYSCRIPT_LAYOUT_HANDLER,
    }
    out = site_dir / RUNTIME_DIR
    out.mkdir(parents=True, exist_ok=True)
    (out / "reactpy-run-config.js").write_text(
        f"export const RUNTIME = {json.dumps(payload)};\n"
        "export const CONFIG_URL = import.meta.url;\n",
        encoding="utf-8",
    )
