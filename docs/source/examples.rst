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


**Local Python File**

.. code-block::

    import idom
    from idom.server.sanic import PerClientStateServer

    def display(element, *args, **kwargs):
        PerClientStateServer(element, *args, **kwargs).run("127.0.0.1", 8765)

    @idom.element
    def Main(self):
        # define your element here
        ...

    if __name__ == "__main__":
        display(Main)


**Jupyter Notebook**

.. code-block::

    from idom.widgets.jupyter import init_display
    display = init_display("127.0.0.1")

    @idom.element
    def MyElement():
        # define your element here
        ...

    jupyter_widget = display(MyElement)

.. note::

    The ``init_display`` function checks environment variables to try and infer whether
    it's in a Jupyterhub instance (e.g. mybinder.org) and if so, assumes the presence of a
    `jupyter_server_proxy <https://github.com/jupyterhub/jupyter-server-proxy>`_. If this
    doesn't work please `post an issue <https://github.com/rmorshea/idom/issues>`_.


Slideshow
---------

Try clicking the image 🖱️

.. example:: slideshow


Click Counter
-------------

.. example:: click_count


To Do List
----------

Try typing in the text box and pressing 'Enter' 📋

.. example:: todo


The Game Snake
--------------

Click to start playing and use the arrow keys to move 🎮

Slow internet may cause inconsistent frame pacing 😅

.. example:: snake_game


Matplotlib Plot
---------------

Pick the polynomial coefficients (seperate each coefficient by a space) 🔢:

.. example:: matplotlib_plot


Simple Dashboard
----------------

Try interacting with the sliders 📈

.. example:: simple_dashboard


Install Javascript Modules
--------------------------

Simply install your javascript library of choice using the ``idom`` CLI:

.. code-block:: bash

    idom install victory

Then import the module with :class:`~idom.widgets.utils.Module`:

.. example:: victory_chart


Define Javascript Modules
-------------------------

Assuming you already installed ``victory`` as in the :ref:`Install Javascript Modules` section:

Click the bars to trigger an event 👇

.. example:: custom_chart


Shared Client Views
-------------------

This example requires the :class:`~idom.server.sanic.SharedClientStateServer`. Be sure
to replace it in your boilerplate code before going further! Once you've done this we
can just re-display our :ref:`Slideshow` example using the new server. Now all we need
to do is connect to the server with a couple clients to see that their views are synced.
This can be done by navigating to the server URL in seperate browser tabs. Likewise if
you're using a Jupyter Notebook you would display it in multiple cells like this:

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


Material UI Slider
------------------

Assuming you already installed ``@material-ui/core`` as in the :ref:`Install Javascript Modules` section:

Move the slider and see the event information update 👇

.. example:: material_ui_slider


Semantic UI Buttons
-------------------

Assuming you already installed ``semantic-ui-react`` as in the :ref:`Install Javascript Modules` section:

Click the buttons and see the event information update 👇

.. example:: primary_secondary_buttons


.. Links
.. =====

.. |launch-binder| image:: https://mybinder.org/badge_logo.svg
 :target: https://mybinder.org/v2/gh/rmorshea/idom/master?filepath=examples%2Fintroduction.ipynb
