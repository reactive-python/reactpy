import asyncio
import os
import threading

from sphinx_autobuild.cli import (
    Server,
    _get_build_args,
    _get_ignore_handler,
    find_free_port,
    get_builder,
    get_parser,
)

from docs.app import IDOM_MODEL_SERVER_URL_PREFIX, Example, make_app, reload_examples
from idom.server.sanic import configure, serve_development_app
from idom.testing import clear_idom_web_modules_dir


# these environment variable are used in custom Sphinx extensions
os.environ["IDOM_DOC_EXAMPLE_SERVER_HOST"] = "127.0.0.1:5555"
os.environ["IDOM_DOC_STATIC_SERVER_HOST"] = ""

_running_idom_servers = []


def wrap_builder(old_builder):
    # This is the bit that we're injecting to get the example components to reload too

    app = make_app()

    configure(
        app,
        Example,
        {"cors": True, "url_prefix": IDOM_MODEL_SERVER_URL_PREFIX},
    )

    thread_started = threading.Event()

    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        server_started = asyncio.Event()

        async def set_thread_event_when_started():
            await server_started.wait()
            thread_started.set()

        loop.run_until_complete(
            asyncio.gather(
                serve_development_app(app, "127.0.0.1", 5555, server_started),
                set_thread_event_when_started(),
            )
        )

    threading.Thread(target=run_in_thread, daemon=True).start()

    thread_started.wait()

    def new_builder():
        clear_idom_web_modules_dir()
        reload_examples()
        old_builder()

    return new_builder


def main():
    # Mostly copied from https://github.com/executablebooks/sphinx-autobuild/blob/b54fb08afc5112bfcda1d844a700c5a20cd6ba5e/src/sphinx_autobuild/cli.py
    parser = get_parser()
    args = parser.parse_args()

    srcdir = os.path.realpath(args.sourcedir)
    outdir = os.path.realpath(args.outdir)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    server = Server()

    build_args, pre_build_commands = _get_build_args(args)
    builder = wrap_builder(
        get_builder(server.watcher, build_args, pre_build_commands=pre_build_commands)
    )

    ignore_handler = _get_ignore_handler(args)
    server.watch(srcdir, builder, ignore=ignore_handler)
    for dirpath in args.additional_watched_dirs:
        dirpath = os.path.realpath(dirpath)
        server.watch(dirpath, builder, ignore=ignore_handler)
    server.watch(outdir, ignore=ignore_handler)

    if not args.no_initial_build:
        builder()

    # Find the free port
    portn = args.port or find_free_port()
    if args.openbrowser is True:
        server.serve(port=portn, host=args.host, root=outdir, open_url_delay=args.delay)
    else:
        server.serve(port=portn, host=args.host, root=outdir)


if __name__ == "__main__":
    main()
