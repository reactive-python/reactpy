from pathlib import Path

from reactpy.executors.asgi import ReactPyCsr

# start
my_app = ReactPyCsr(
    Path(__file__).parent / "root.py",
    initial="Loading...",
    root_name="root",
)
