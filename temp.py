from idom import component, html, run
from idom.server import starlette as server


@component
def ShowLocation():
    loc = server.use_location()
    return html.h1(str(loc.pathname + loc.search))


run(ShowLocation, implementation=server)
