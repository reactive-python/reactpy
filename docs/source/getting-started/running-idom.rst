Running IDOM
============

The simplest way to run IDOM is with the :func:`idom.server.prefab.run` function. By
default this will run your application using the first builtin server implementation
whose dependencies have all been installed. Running a tiny "hello world" application
just requires the following code:

.. example:: hello_world
    :activate-result:

Running IDOM in this way could be somewhat unpredictable though, since the kind of
server being used depends on what gets discovered first. To be more explicit about which
to use you can import your chosen server implementation and pass it to the
``server_type`` parameter of ``run()``:

.. code-block::

    import idom
    from idom.server.sanic import PerClientStateServer

    idom.run(App, server_type=PerClientStateServer)

Presently IDOM's core library supports the following server implementations:

- ``fastapi``
- ``sanic``
- ``flask``
- ``tornado``

.. note::

    See :ref:`here <Installing Other Servers>` for information on how to install
    their dependencies.


Configuring IDOM
----------------

Under construction :)


Add to Existing Applications
----------------------------

IDOM provides a Javascript client called ``idom-client-react`` that can be used to embed
IDOM views within an existing applications. This is actually how the interactive
examples throughout this documentation have been created. You can try this out by
embedding one the examples from this documentation into your own webpage:

.. tab-set::

    .. tab-item:: HTML

        .. literalinclude:: _static/embed.html
            :language: html

    .. tab-item:: ▶️ Result

        .. raw:: html
            :file: _static/embed.html

.. note::

    For more information on how to use the client see the :ref:`Javascript API` reference.

As mentioned though, this is connecting to the server that is hosting this
documentation, as indicated by the ``wss://idom-docs.herokuapp.com`` web socket URL. If
you want to connect to a view from your own server, you'll need to change the URL above
to one you provide...


Add IDOM to Your Existing Python Server
---------------------------------------

If you're already serving an application with one of the supported web servers listed
above, you can add an IDOM to them as a server extension. Instead of using the ``run()``
function, you'll instantiate one of IDOM's server implementations by passing it an
instance of your existing application:

.. code-block::

    from sanic import Sanic

    from idom import component, html
    from idom.server.fastapi import PerClientStateServer, Config

    existing_app = Sanic(__name__)

    @component
    def IdomView(view_id=None):
        return html.div(
            html.h1("This is an IDOM App")
            html.p("Given view ID: ", html.code(repr(view_id)))
        )

    PerClientStateServer(IdomView, app=existing_app, config=Config(url_prefix="_idom"))

    existing_app.run(host="127.0.0.1", port=8000)

To test that everything is working, you should be able to navigate to
``https://127.0.0.1:8000/_idom`` where you should see the results from ``IdomView``.

