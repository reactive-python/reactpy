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
    for file in EXAMPLES_DIR.rglob("*.py"):
        yield get_example_name_from_file(file), load_one_example(file)


def all_example_names() -> set[str]:
    return {get_example_name_from_file(file) for file in EXAMPLES_DIR.rglob("*.py")}


def load_one_example(file_or_name: Path | str) -> Callable[[], ComponentType]:
    if isinstance(file_or_name, str):
        file = get_py_example_file_by_name(file_or_name)
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
        code = compile(file.read_text(), str(file.absolute()), "exec")
        exec(code, {"print": capture_print})
    except Exception:
        return _make_error_display()
    finally:
        idom.run = RUN_IDOM

    if captured_component_constructor is None:
        return _make_example_did_not_run(str(file))
    else:

        @idom.component
        def Wrapper():
            return idom.html.div(captured_component_constructor(), ShowPrint())

        return Wrapper


def get_example_name_from_file(file: Path) -> str:
    return ".".join(file.relative_to(EXAMPLES_DIR).with_suffix("").parts)


def get_py_example_file_by_name(name: str) -> Path:
    return EXAMPLES_DIR.joinpath(*name.split(".")).with_suffix(".py")


def get_js_example_file_by_name(name: str) -> Path:
    return EXAMPLES_DIR.joinpath(*name.split(".")).with_suffix(".js")


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


def _make_error_display():
    @idom.component
    def ShowError():
        return idom.html.pre(format_exc())

    return ShowError
