import asyncio

from idom import component, html, run
from idom.backend.starlette import (
    configure,
    create_development_app,
    serve_development_app,
)


@component
def temp():
    return html.h1("asd")


app = create_development_app()
configure(app, temp)
asyncio.run(serve_development_app(app, "localhost", 8000))
