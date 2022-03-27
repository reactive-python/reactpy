# :lines: 11-

from idom import run
from idom.server import tornado as tornado_server


# the run() function is the entry point for examples
tornado_server.configure = lambda _, cmpt: run(cmpt)


import tornado.ioloop
import tornado.web

from idom import component, html
from idom.server.tornado import configure


@component
def HelloWorld():
    return html.h1("Hello, world!")


def make_app():
    app = tornado.web.Application()
    configure(app, HelloWorld)
    return app


if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()
