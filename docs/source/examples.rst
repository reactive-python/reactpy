Examples
========

You can find the following examples and more on binder |launch-binder|:

.. contents::
  :local:
  :depth: 1


Display Function
----------------

Depending on how you plan to use these examples you'll need different
boilerplate code.

In all cases we define a ``display(element)`` function which will display the
view. In a Jupyter Notebook it will appear in an output cell. If you're running
``idom`` as a webserver it will appear at http://localhost:8765/client/index.html.

.. note::

  The :ref:`Shared Client Views` example requires ``SharedClientStateServer`` server instead
  of the ``PerClientStateServer`` server shown in the boilerplate below. Be sure to wwap it
  out when you get there.


**Jupyter Notebook (localhost)**

.. code-block::

    from idom.server import multiview_server
    from idom.server.sanic import PerClientStateServer

    host, port = "127.0.0.1", 8765
    mount, server = multiview_server(
        PerClientStateServer, host, port, {"cors": True}, {"access_log": False}
    )
    server_url = f"http://{host}:{port}"


    def display(element, *args, **kwargs):
        view_id = mount(element, *args, **kwargs)
        return idom.JupyterDisplay(server_url, {"view_id": view_id})



**Jupyter Notebook (binder.org)**

.. code-block::

    import os
    from typing import Mapping, Any, Optional

    from idom.server import multiview_server
    from idom.server.sanic import PerClientStateServer


    def example_server_url(host: str, port: int) -> str:
        localhost_idom_path = f"http://{host}:{port}"
        jupyterhub_idom_path = path_to_jupyterhub_proxy(port)
        return jupyterhub_idom_path or localhost_idom_path


    def path_to_jupyterhub_proxy(port: int) -> Optional[str]:
        """If running on Jupyterhub return the path from the host's root to a proxy server

        This is used when examples are running on mybinder.org or in a container created by
        jupyter-repo2docker. For this to work a ``jupyter_server_proxy`` must have been
        instantiated. See https://github.com/jupyterhub/jupyter-server-proxy
        """
        if "JUPYTERHUB_OAUTH_CALLBACK_URL" in os.environ:
            url = os.environ["JUPYTERHUB_OAUTH_CALLBACK_URL"].rsplit("/", 1)[0]
            return f"{url}/proxy/{port}"
        elif "JUPYTER_SERVER_URL" in os.environ:
            return f"{os.environ['JUPYTER_SERVER_URL']}/proxy/{port}"
        else:
            return None


    host, port = "127.0.0.1", 8765
    mount, server = multiview_server(
        PerClientStateServer, host, port, {"cors": True}, {"access_log": False}
    )
    server_url = example_server_url(host, port)


    def display(element, *args, **kwargs):
        view_id = mount(element, *args, **kwargs)
        print(f"View ID: {view_id}")
        return idom.JupyterDisplay("jupyter", server_url, {"view_id": view_id})


**Local Python File**

.. code-block::

    import idom
    from idom.server.sanic import PerClientStateServer

    def display(element, *args, **kwargs):
        PerClientStateServer(element, *args, **kwargs).run("127.0.0.1", 8765)

    @idom.element
    async def Main(self):
        # define your element here
        ...

    if __name__ == "__main__":
        display(Main)


Slideshow
---------

.. literalinclude:: widgets/slideshow.py

Try clicking the image 🖱️

.. interactive-widget:: slideshow


To Do List
----------

.. literalinclude:: widgets/todo.py

Try typing in the text box and pressing 'Enter' 📋

.. interactive-widget:: todo


Drag and Drop
-------------

.. literalinclude:: widgets/drag_and_drop.py

Click and drag the black box onto the white one 👆

.. interactive-widget:: drag_and_drop


The Game Snake
--------------

.. literalinclude:: widgets/snake.py

Click to start playing and use the arrow keys to move 🎮

Slow internet may cause inconsistent frame pacing 😅

.. interactive-widget:: snake


Plotting with Matplotlib
------------------------

.. literalinclude:: widgets/matplotlib_animation.py

Try interacting with the sliders 📈

.. interactive-widget:: matplotlib_animation


Install Javascript Modules
--------------------------

Simply install your javascript library of choice using the ``idom`` CLI:

.. code-block:: bash

    idom install victory

Then import the module with :class:`idom.widgets.utils.Module`:

.. literalinclude:: widgets/victory_chart.py

.. note::

    It's possible to install the module at runtime by specifying ``install=True``.
    However this is generally discouraged.

.. interactive-widget:: victory_chart


Define Javascript Modules
-------------------------

Assuming you already installed ``victory`` as in the :ref:`Install Javascript Modules` section:

.. literalinclude:: widgets/custom_chart.py

Click the bars to trigger an event 👇

.. interactive-widget:: custom_chart

Source of ``chart.js``:

.. literalinclude:: widgets/custom_chart.js
    :language: javascript


Shared Client Views
-------------------

This example requires the :ref:`idom.server.sanic.SharedClientState` server. Be sure to
replace it in your boilerplate code before going further! Once you've done this we can
just re-display our :ref:`Slideshow` example using the new server. Now all we need to do
is connect to the server with a couple clients to see that their views are synced. This
can be done by navigating to the server URL in seperate browser tabs. Likewise if you're
using a Jupyter Notebook you would display it in multiple cells like this:

**Jupyter Notebook**

.. code-block::

    # Cell 1
    ...  # boiler plate with SharedClientState server

    # Cell 2
    ...  # code from the Slideshow example

    # Cell 3
    widget = display(Slideshow)

    # Cell 4
    widget  # this is our first view

    # Cell 5
    widget  # this is out second view


.. Links
.. =====

.. |launch-binder| image:: https://mybinder.org/badge_logo.svg
 :target: https://mybinder.org/v2/gh/rmorshea/idom/master?filepath=examples%2Fintroduction.ipynb
