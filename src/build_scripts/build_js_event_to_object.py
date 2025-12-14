# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
import pathlib
import subprocess
import sys

dev_mode = "--dev" in sys.argv
root_dir = pathlib.Path(__file__).parent.parent.parent
build_commands = [
    [
        "bun",
        "install",
        "--cwd",
        "src/js/packages/event-to-object",
        *([] if dev_mode else ["--production"]),
    ],
    [
        "bun",
        "run",
        "--cwd",
        "src/js/packages/event-to-object",
        "build",
    ],
]

for command in build_commands:
    print(f"Running command: '{command}'...")  # noqa: T201
    subprocess.run(command, check=True, cwd=root_dir)  # noqa: S603
