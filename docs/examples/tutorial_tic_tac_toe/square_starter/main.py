from pathlib import Path

from app import square

from reactpy import html
from reactpy.executors.asgi import ReactPy

# ReactPy serves the components, not the files on your disk, so the stylesheet
# is read here and injected into the page's <head>.
CSS = Path("styles.css").read_text()

my_app = ReactPy(square, html_head=html.head(html.style(CSS)))
