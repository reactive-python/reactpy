import idom
from idom.server import sanic as server


@idom.component
def HelloWorld():
    print(server.use_scope())
    return idom.html.h1("Hello, world!")


idom.run(HelloWorld, implementation=server)
