import sys
import time
from os.path import getmtime
from pathlib import Path
from threading import Thread

import idom
from idom.widgets import hotswap


here = Path(__file__).parent
examples_dir = here.parent / "docs" / "source" / "examples"
sys.path.insert(0, str(examples_dir))

for file in examples_dir.iterdir():
    if not file.is_file() or not file.suffix == ".py" or file.stem.startswith("_"):
        continue


def on_file_change(path, callback):
    def watch_for_change():
        last_modified = 0
        while True:
            modified_at = getmtime(path)
            if modified_at != last_modified:
                callback()
                last_modified = modified_at
            time.sleep(1)

    Thread(target=watch_for_change, daemon=True).start()


def main():
    try:
        ex_name = sys.argv[1]
    except IndexError:
        print("No example argument given. Choose from:")
        _print_available_options()
        return

    example_file = examples_dir / (ex_name + ".py")

    if not example_file.exists():
        print(f"No example {ex_name!r} exists. Choose from:")
        _print_available_options()
        return

    idom_run = idom.run
    idom.run, component = hotswap(update_on_change=True)

    def update_component():
        print(f"Reloading {ex_name}")
        with example_file.open() as f:
            exec(
                f.read(),
                {
                    "__file__": str(file),
                    "__name__": f"__main__.examples.{file.stem}",
                },
            )

    on_file_change(example_file, update_component)

    idom_run(component, port=8000)


def _print_available_options():
    for found_example_file in examples_dir.glob("*.py"):
        print("-", found_example_file.stem)


if __name__ == "__main__":
    main()
