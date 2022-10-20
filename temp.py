from idom import component, html, run
from idom.backend import fastapi, flask, sanic, starlette, tornado


@component
def root():
    return html.h1("hello")


run(root, implementation=starlette)
