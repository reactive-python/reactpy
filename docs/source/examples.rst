Examples
========

You can also try these examples out on binder |launch-binder|:

.. contents::
  :local:
  :depth: 1


Displaying These Examples
-------------------------

Depending on how you plan to use these examples you'll need different
boilerplate code.

In all cases we define a ``display(element)`` function which will display the
view. In a Jupyter Notebook it will appear in an output cell. If you're running
``idom`` as a webserver it will appear at http://localhost:8765/client/index.html.


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


Material UI Slider
------------------

Assuming you already installed ``@material-ui/core`` as in the :ref:`Install Javascript Modules` section:

Move the slider and see the event information update 👇

.. example:: material_ui_slider


.. Links
.. =====

.. |launch-binder| image:: https://mybinder.org/badge_logo.svg
 :target: https://mybinder.org/v2/gh/rmorshea/idom/master?filepath=examples%2Fintroduction.ipynb
