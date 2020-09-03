IDOM |release|
==============

.. image:: branding/idom-logo.png
    :height: 250px

Libraries for defining and controlling interactive webpages with Python
3.7 and above.

.. toctree::
    :maxdepth: 1

    installation
    getting-started
    core-concepts
    life-cycle-hooks
    javascript-modules
    specifications
    extra-features
    examples
    known-issues
    api


Try it Now!
-----------

- In a Jupyter Notebook - |launch-binder|

- Using working :ref:`examples <Examples>`


Early Days
----------

IDOM is still young. If you have ideas or find a bug, be sure to post an
`issue`_ or create a `pull request`_. Thanks in advance!


At a Glance
-----------

Let's use IDOM to create a simple slideshow which changes whenever a
user clicks an image:

.. code-block::

    import idom

    @idom.element
    async def Slideshow():
        index, set_index = idom.hooks.use_state(0)

        def next_image(event):
            set_index(index + 1)

        return idom.html.img(
            {
                "src": f"https://picsum.photos/800/300?image={index}",
                "style": {"cursor": "pointer"},
                "onClick": next_image,
            }
        )

    host, port = "localhost", 8765
    server = idom.server.sanic.PerClientStateServer(Slideshow)
    server.run(host, port)

Running this will serve our slideshow to ``"https://localhost:8765"``. You can try out
a working example by enabling the widget below. Once enabled clicking the image will
cause the widget to change 🖱️

.. interactive-widget:: slideshow

.. note::

    You can display the same thing in a Jupyter Notebook using widgets!

    .. code-block::

        idom.JupyterDisplay(f"https://{host}:{port}")

    For info on working with IDOM in Jupyter see some :ref:`examples <Display Function>`.


.. Links
.. =====

.. _issue: https://github.com/rmorshea/idom/issues
.. _pull request: https://github.com/rmorshea/idom/pulls
.. _IDOM Sandbox: https://idom-sandbox.herokuapp.com
.. |launch-binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/rmorshea/idom/master?filepath=notebooks%2Fintroduction.ipynb
