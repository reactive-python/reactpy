from __future__ import annotations

from io import StringIO
from pathlib import Path
from traceback import format_exc
from typing import Callable, Iterator

import idom
from idom import ComponentType


HERE = Path(__file__)
EXAMPLES_DIR = HERE.parent / "source" / "_examples"
RUN_IDOM = idom.run


def load_examples() -> Iterator[tuple[str, Callable[[], ComponentType]]]:
    for name in all_example_names():
        yield name, load_one_example(name)


def all_example_names() -> set[str]:
    names = set()
    for file in EXAMPLES_DIR.rglob("*.py"):
        if file.name != "app.py" and (file.parent / "app.py").exists():
            # this isn't the main example file
            continue
        path = file.relative_to(EXAMPLES_DIR)
        if path.name == "app.py":
            path = path.parent
        else:
            path = path.with_suffix("")
        names.add(".".join(path.parts))
    return names


def load_one_example(file_or_name: Path | str) -> Callable[[], ComponentType]:
    if isinstance(file_or_name, str):
        file = get_main_example_file_by_name(file_or_name)
    else:
        file = file_or_name

    if not file.exists():
        raise FileNotFoundError(str(file))

    captured_component_constructor = None
    capture_print, ShowPrint = _printout_viewer()

    def capture_component(component_constructor):
        nonlocal captured_component_constructor
        captured_component_constructor = component_constructor

    idom.run = capture_component
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
        idom.run = RUN_IDOM

    if captured_component_constructor is None:
        return _make_example_did_not_run(str(file))
    else:

        @idom.component
        def Wrapper():
            return idom.html.div(captured_component_constructor(), ShowPrint())

        return Wrapper


def get_main_example_file_by_name(name: str) -> Path:
    path = _get_root_example_path_by_name(name)
    if path.is_dir():
        return path / "app.py"
    else:
        return path.with_suffix(".py")


def get_example_files_by_name(name: str) -> list[Path]:
    path = _get_root_example_path_by_name(name)
    if path.is_dir():
        return list(path.glob("*"))
    path = path.with_suffix(".py")
    return [path] if path.exists() else []


def _get_root_example_path_by_name(name: str) -> Path:
    return EXAMPLES_DIR.joinpath(*name.split("."))


def _printout_viewer():
    print_callbacks: set[Callable[[str], None]] = set()

    @idom.component
    def ShowPrint():
        buffer = idom.hooks.use_state(StringIO)[0]
        update = _use_force_update()

        @idom.hooks.use_effect
        def add_buffer():
            print_callbacks.add(buffer.write)
            update()

        value = buffer.getvalue()
        return idom.html.pre({"class": "printout"}, value) if value else idom.html.div()

    def capture_print(*args, **kwargs):
        buffer = StringIO()
        print(*args, file=buffer, **kwargs)
        value = buffer.getvalue()
        for cb in print_callbacks:
            cb(value)

    return capture_print, ShowPrint


def _use_force_update():
    toggle, set_toggle = idom.hooks.use_state(False)
    return lambda: set_toggle(not toggle)


def _make_example_did_not_run(example_name):
    @idom.component
    def ExampleDidNotRun():
        return idom.html.code(f"Example {example_name} did not run")

    return ExampleDidNotRun


def _make_error_display(message):
    @idom.component
    def ShowError():
        return idom.html.pre(message)

    return ShowError
