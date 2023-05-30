from __future__ import annotations

from collections.abc import Iterator
from io import StringIO
from pathlib import Path
from traceback import format_exc
from typing import Callable

import reactpy
from reactpy.types import ComponentType

HERE = Path(__file__)
SOURCE_DIR = HERE.parent / "source"
CONF_FILE = SOURCE_DIR / "conf.py"
RUN_ReactPy = reactpy.run


def load_examples() -> Iterator[tuple[str, Callable[[], ComponentType]]]:
    for name in all_example_names():
        yield name, load_one_example(name)


def all_example_names() -> set[str]:
    names = set()
    for file in _iter_example_files(SOURCE_DIR):
        path = file.parent if file.name == "main.py" else file
        names.add("/".join(path.relative_to(SOURCE_DIR).with_suffix("").parts))
    return names


def load_one_example(file_or_name: Path | str) -> Callable[[], ComponentType]:
    return lambda: (
        # we use a lambda to ensure each instance is fresh
        _load_one_example(file_or_name)
    )


def get_normalized_example_name(
    name: str, relative_to: str | Path | None = SOURCE_DIR
) -> str:
    return "/".join(
        _get_root_example_path_by_name(name, relative_to).relative_to(SOURCE_DIR).parts
    )


def get_main_example_file_by_name(
    name: str, relative_to: str | Path | None = SOURCE_DIR
) -> Path:
    path = _get_root_example_path_by_name(name, relative_to)
    if path.is_dir():
        return path / "main.py"
    else:
        return path.with_suffix(".py")


def get_example_files_by_name(
    name: str, relative_to: str | Path | None = SOURCE_DIR
) -> list[Path]:
    path = _get_root_example_path_by_name(name, relative_to)
    if path.is_dir():
        return [p for p in path.glob("*") if not p.is_dir()]
    else:
        path = path.with_suffix(".py")
        return [path] if path.exists() else []


def _iter_example_files(root: Path) -> Iterator[Path]:
    for path in root.iterdir():
        if path.is_dir():
            if not path.name.startswith("_") or path.name == "_examples":
                yield from _iter_example_files(path)
        elif path.suffix == ".py" and path != CONF_FILE:
            yield path


def _load_one_example(file_or_name: Path | str) -> ComponentType:
    if isinstance(file_or_name, str):
        file = get_main_example_file_by_name(file_or_name)
    else:
        file = file_or_name

    if not file.exists():
        raise FileNotFoundError(str(file))

    print_buffer = _PrintBuffer()

    def capture_print(*args, **kwargs):
        buffer = StringIO()
        print(*args, file=buffer, **kwargs)
        print_buffer.write(buffer.getvalue())

    captured_component_constructor = None

    def capture_component(component_constructor):
        nonlocal captured_component_constructor
        captured_component_constructor = component_constructor

    reactpy.run = capture_component
    try:
        code = compile(file.read_text(), str(file), "exec")
        exec(
            code,
            {
                "print": capture_print,
                "__file__": str(file),
                "__name__": file.stem,
            },
        )
    except Exception:
        return _make_error_display(format_exc())
    finally:
        reactpy.run = RUN_ReactPy

    if captured_component_constructor is None:
        return _make_example_did_not_run(str(file))

    @reactpy.component
    def Wrapper():
        return reactpy.html.div(captured_component_constructor(), PrintView())

    @reactpy.component
    def PrintView():
        text, set_text = reactpy.hooks.use_state(print_buffer.getvalue())
        print_buffer.set_callback(set_text)
        return (
            reactpy.html.pre({"class_name": "printout"}, text)
            if text
            else reactpy.html.div()
        )

    return Wrapper()


def _get_root_example_path_by_name(name: str, relative_to: str | Path | None) -> Path:
    if not name.startswith("/") and relative_to is not None:
        rel_path = Path(relative_to)
        rel_path = rel_path.parent if rel_path.is_file() else rel_path
    else:
        rel_path = SOURCE_DIR
    return rel_path.joinpath(*name.split("/")).resolve()


class _PrintBuffer:
    def __init__(self, max_lines: int = 10):
        self._callback = None
        self._lines = ()
        self._max_lines = max_lines

    def set_callback(self, function: Callable[[str], None]) -> None:
        self._callback = function

    def getvalue(self) -> str:
        return "".join(self._lines)

    def write(self, text: str) -> None:
        if len(self._lines) == self._max_lines:
            self._lines = self._lines[1:] + (text,)
        else:
            self._lines += (text,)
        if self._callback is not None:
            self._callback(self.getvalue())


def _make_example_did_not_run(example_name):
    @reactpy.component
    def ExampleDidNotRun():
        return reactpy.html.code(f"Example {example_name} did not run")

    return ExampleDidNotRun()


def _make_error_display(message):
    @reactpy.component
    def ShowError():
        return reactpy.html.pre(message)

    return ShowError()
