Examples
========

You can find the following examples and more on binder |launch-binder|:

.. contents::
  :local:
  :depth: 1


**Display Function**
--------------------

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

.. literalinclude:: examples/slideshow.py

Try clicking the image 🖱️

.. interactive-widget:: slideshow


Click Counter
-------------

.. literalinclude:: examples/click_count.py

.. interactive-widget:: click_count


To Do List
----------

.. literalinclude:: examples/todo.py

Try typing in the text box and pressing 'Enter' 📋

.. interactive-widget:: todo


The Game Snake
--------------

.. literalinclude:: examples/snake_game.py

Click to start playing and use the arrow keys to move 🎮

Slow internet may cause inconsistent frame pacing 😅

.. interactive-widget:: snake_game


Matplotlib Plot
---------------

.. literalinclude:: examples/matplotlib_plot.py

Pick the polynomial coefficients (seperate each coefficient by a space) 🔢:

.. interactive-widget:: matplotlib_plot


Simple Dashboard
----------------

.. literalinclude:: examples/simple_dashboard.py

Try interacting with the sliders 📈

.. interactive-widget:: simple_dashboard


Install Javascript Modules
--------------------------

Simply install your javascript library of choice using the ``idom`` CLI:

.. code-block:: bash

    idom install victory

Then import the module with :class:`~idom.widgets.utils.Module`:

.. literalinclude:: examples/victory_chart.py

.. note::

    It's possible to install the module at runtime by specifying ``install=True``.
    However this is generally discouraged.

.. interactive-widget:: victory_chart


Define Javascript Modules
-------------------------

Assuming you already installed ``victory`` as in the :ref:`Install Javascript Modules` section:

.. literalinclude:: examples/custom_chart.py

Click the bars to trigger an event 👇

.. interactive-widget:: custom_chart

Source of ``chart.js``:

.. literalinclude:: examples/custom_chart.js
    :language: javascript


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

.. literalinclude:: examples/material_ui_slider.py

Move the slider and see the event information update 👇

.. interactive-widget:: material_ui_slider


Semantic UI Buttons
-------------------

Assuming you already installed ``semantic-ui-react`` as in the :ref:`Install Javascript Modules` section:

.. literalinclude:: examples/primary_secondary_buttons.py

Click the buttons and see the event information update 👇

.. interactive-widget:: primary_secondary_buttons


.. Links
.. =====

.. |launch-binder| image:: https://mybinder.org/badge_logo.svg
 :target: https://mybinder.org/v2/gh/rmorshea/idom/master?filepath=examples%2Fintroduction.ipynb


Example Utilities
-----------------

In some of the examples above you may see this import ``from _utils import *`` the
content of which is shown below:

.. literalinclude:: examples/_utils.py
