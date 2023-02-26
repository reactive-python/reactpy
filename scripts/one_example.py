import sys
import time
from os.path import getmtime
from threading import Event, Thread

import reactpy
from docs.examples import all_example_names, get_example_files_by_name, load_one_example
from reactpy.widgets import _hotswap


EXAMPLE_NAME_SET = all_example_names()
EXAMPLE_NAME_LIST = tuple(sorted(EXAMPLE_NAME_SET))


def on_file_change(path, callback):
    did_call_back_once = Event()

    def watch_for_change():
        last_modified = 0
        while True:
            modified_at = getmtime(path)
            if modified_at != last_modified:
                callback()
                did_call_back_once.set()
                last_modified = modified_at
            time.sleep(1)

    Thread(target=watch_for_change, daemon=True).start()
    did_call_back_once.wait()


def main():
    ex_name = _example_name_input()

    mount, component = _hotswap()

    def update_component():
        print(f"Loading example: {ex_name!r}")
        mount(load_one_example(ex_name))

    for file in get_example_files_by_name(ex_name):
        on_file_change(file, update_component)

    reactpy.run(component)


def _example_name_input() -> str:
    if len(sys.argv) == 1:
        _print_error(
            "No example argument given. Provide an example's number from above."
        )
        sys.exit(1)

    ex_num = sys.argv[1]

    try:
        ex_num = int(ex_num)
    except ValueError:
        _print_error(
            f"No example {ex_num!r} exists. Provide an example's number as an integer."
        )
        sys.exit(1)

    ex_index = ex_num - 1
    try:
        return EXAMPLE_NAME_LIST[ex_index]
    except IndexError:
        _print_error(f"No example #{ex_num} exists. Choose from an option above.")
        sys.exit(1)


def _print_error(*args) -> None:
    _print_available_options()
    print(*args)


def _print_available_options():
    examples_by_path = {}
    for i, name in enumerate(EXAMPLE_NAME_LIST):
        if "/" not in name:
            path = ""
        else:
            path, name = name.rsplit("/", 1)
        examples_by_path.setdefault(path, []).append(name)

    number = 1
    print()
    for path, names in examples_by_path.items():
        title = " > ".join(
            section.replace("-", " ").replace("_", " ").title()
            for section in path.split("/")
            if not section.startswith("_")
        )
        print(title)
        print("-" * len(title))
        for name in names:
            print(f"{number}. ", name)
            number += 1
        print()


if __name__ == "__main__":
    main()
