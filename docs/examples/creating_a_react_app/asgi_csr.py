from pathlib import Path

from reactpy.executors.asgi import ReactPyCsr

my_app = ReactPyCsr(Path(__file__).parent / "root.py", initial="Loading...")
