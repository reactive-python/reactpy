import sys
import time
from os.path import getmtime
from threading import Event, Thread

import idom
from docs.examples import all_example_names, get_example_files_by_name, load_one_example
from idom.widgets import hotswap


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

    mount, component = hotswap(update_on_change=True)

    def update_component():
        print(f"Loading example: {ex_name!r}")
        mount(load_one_example(ex_name))

    for file in get_example_files_by_name(ex_name):
        on_file_change(file, update_component)

    idom.run(component)


def _example_name_input() -> str:
    if len(sys.argv) == 1:
        print("No example argument given. Provide an example's number or name:")
        _print_available_options()
        sys.exit(1)

    ex_name = sys.argv[1]

    if ex_name in EXAMPLE_NAME_SET:
        return ex_name

    try:
        ex_num = int(ex_name)
    except ValueError:
        print(f"No example {ex_name!r} exists. Provide an example's number or name:")
        _print_available_options()
        sys.exit(1)

    ex_index = ex_num - 1
    try:
        return EXAMPLE_NAME_LIST[ex_index]
    except IndexError:
        print(f"No example #{ex_num} exists.")
        sys.exit(1)


def _print_available_options():
    for i, name in enumerate(EXAMPLE_NAME_LIST):
        print(f"{i + 1}.", name)


if __name__ == "__main__":
    main()
