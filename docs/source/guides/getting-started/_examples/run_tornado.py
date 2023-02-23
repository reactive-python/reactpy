# :lines: 11-

from reactpy import run
from reactpy.backend import tornado as tornado_server


# the run() function is the entry point for examples
tornado_server.configure = lambda _, cmpt: run(cmpt)


import tornado.ioloop
import tornado.web

from reactpy import component, html
from reactpy.backend.tornado import configure


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
