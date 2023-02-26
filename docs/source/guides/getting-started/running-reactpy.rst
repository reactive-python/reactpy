Running ReactPy
===============

The simplest way to run ReactPy is with the :func:`~reactpy.backend.utils.run` function. This
is the method you'll see used throughout this documentation. However, this executes your
application using a development server which is great for testing, but probably not what
if you're :ref:`deploying in production <Running ReactPy in Production>`. Below are some
more robust and performant ways of running ReactPy with various supported servers.


Running ReactPy in Production
-----------------------------

The first thing you'll need to do if you want to run ReactPy in production is choose a
backend implementation and follow its documentation on how to create and run an
application. This is the backend :ref:`you probably chose <Native Backends>` when
installing ReactPy. Then you'll need to configure that application with an ReactPy view. We
show the basics of how to set up, and then run, each supported backend below, but all
implementations will follow a pattern similar to the following:

.. code-block::

    from my_chosen_backend import Application

    from reactpy import component, html
    from reactpy.backend.my_chosen_backend import configure


    @component
    def HelloWorld():
        return html.h1("Hello, world!")


    app = Application()
    configure(app, HelloWorld)

You'll then run this ``app`` using an `ASGI <https://asgi.readthedocs.io/en/latest/>`__
or `WSGI <https://wsgi.readthedocs.io/>`__ server from the command line.


Running with `FastAPI <https://fastapi.tiangolo.com>`__
.......................................................

.. reactpy:: _examples/run_fastapi

Then assuming you put this in ``main.py``, you can run the ``app`` using the `Uvicorn
<https://www.uvicorn.org/>`__ ASGI server:

.. code-block:: bash

    uvicorn main:app


Running with `Flask <https://palletsprojects.com/p/flask/>`__
.............................................................

.. reactpy:: _examples/run_flask

Then assuming you put this in ``main.py``, you can run the ``app`` using the `Gunicorn
<https://gunicorn.org/>`__ WSGI server:

.. code-block:: bash

    gunicorn main:app


Running with `Sanic <https://sanicframework.org>`__
...................................................

.. reactpy:: _examples/run_sanic

Then assuming you put this in ``main.py``, you can run the ``app`` using Sanic's builtin
server:

.. code-block:: bash

    sanic main.app


Running with `Starlette <https://www.starlette.io/>`__
......................................................

.. reactpy:: _examples/run_starlette

Then assuming you put this in ``main.py``, you can run the application using the
`Uvicorn <https://www.uvicorn.org/>`__ ASGI server:

.. code-block:: bash

    uvicorn main:app


Running with `Tornado <https://www.tornadoweb.org/en/stable/>`__
................................................................

.. reactpy:: _examples/run_tornado

Tornado is run using it's own builtin server rather than an external WSGI or ASGI
server.


Running ReactPy in Debug Mode
-----------------------------

ReactPy provides a debug mode that is turned off by default. This can be enabled when you
run your application by setting the ``REACTPY_DEBUG_MODE`` environment variable.

.. tab-set::

    .. tab-item:: Unix Shell

        .. code-block::

            export REACTPY_DEBUG_MODE=1
            python my_reactpy_app.py

    .. tab-item:: Command Prompt

        .. code-block:: text

            set REACTPY_DEBUG_MODE=1
            python my_reactpy_app.py

    .. tab-item:: PowerShell

        .. code-block:: powershell

            $env:REACTPY_DEBUG_MODE = "1"
            python my_reactpy_app.py

.. danger::

    Leave debug mode off in production!

Among other things, running in this mode:

- Turns on debug log messages
- Adds checks to ensure the :ref:`VDOM` spec is adhered to
- Displays error messages that occur within your app

Errors will be displayed where the uppermost component is located in the view:

.. reactpy:: _examples/debug_error_example


Backend Configuration Options
-----------------------------

ReactPy's various backend implementations come with ``Options`` that can be passed to their
respective ``configure()`` functions in the following way:

.. code-block::

    from reactpy.backend.<implementation> import configure, Options

    configure(app, MyComponent, Options(...))

To learn more read about the options for your chosen backend ``<implementation>``:

- :class:`reactpy.backend.fastapi.Options`
- :class:`reactpy.backend.flask.Options`
- :class:`reactpy.backend.sanic.Options`
- :class:`reactpy.backend.starlette.Options`
- :class:`reactpy.backend.tornado.Options`


Embed in an Existing Webpage
----------------------------

ReactPy provides a Javascript client called ``@reactpy/client`` that can be used to embed
ReactPy views within an existing applications. This is actually how the interactive
examples throughout this documentation have been created. You can try this out by
embedding one the examples from this documentation into your own webpage:

.. tab-set::

    .. tab-item:: HTML

        .. literalinclude:: _static/embed-doc-ex.html
            :language: html

    .. tab-item:: ▶️ Result

        .. raw:: html
            :file: _static/embed-doc-ex.html

.. note::

    For more information on how to use the client see the :ref:`Javascript API`
    reference. Or if you need to, your can :ref:`write your own backend implementation
    <writing your own backend>`.

As mentioned though, this is connecting to the server that is hosting this
documentation. If you want to connect to a view from your own server, you'll need to
change the URL above to one you provide. One way to do this might be to add to an
existing application. Another would be to run ReactPy in an adjacent web server instance
that you coordinate with something like `NGINX <https://www.nginx.com/>`__. For the sake
of simplicity, we'll assume you do something similar to the following in an existing
Python app:

.. tab-set::

    .. tab-item:: main.py

        .. literalinclude:: _static/embed-reactpy-view/main.py
            :language: python

    .. tab-item:: index.html

        .. literalinclude:: _static/embed-reactpy-view/index.html
            :language: html

After running ``python main.py``, you should be able to navigate to
``http://127.0.0.1:8000/index.html`` and see:

.. card::
    :text-align: center

    .. image:: _static/embed-reactpy-view/screenshot.png
        :width: 500px

