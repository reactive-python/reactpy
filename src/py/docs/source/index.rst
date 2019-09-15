IDOM |release|
==============

.. image:: branding/idom-logo.png
    :height: 250px

Libraries for defining and controlling interactive webpages with Python
3.6 and above.

.. toctree::
    :maxdepth: 1

    install
    basics
    concepts
    examples
    specs
    glossary
    api


Try it Now!
-----------

- In a Jupyter Notebook - |launch-binder|

- With an online editor - `IDOM Sandbox`_


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
    async def Slideshow(self, index=0):

        async def next_image(event):
            self.update(index + 1)

        url = f"https://picsum.photos/800/300?image={index}"
        return idom.node("img", src=url, onChange=next_image)

    server = idom.server.sanic.PerClientState(Slideshow)
    server.daemon("localhost", 8765).join()

Running this will serve our slideshow to
``"https://localhost:8765/client/index.html"``

.. image:: https://picsum.photos/700/300?random

You could even display the same thing in a Jupyter notebook!

.. code-block::

   idom.display("jupyter", "https://localhost:8765/stream")

Every click will then cause the image to change (it won’t here of
course).


.. Links
.. =====

.. _issue: https://github.com/rmorshea/idom/issues
.. _pull request: https://github.com/rmorshea/idom/pulls
.. _IDOM Sandbox: https://idom-sandbox.herokuapp.com
.. |launch-binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/rmorshea/idom/master?filepath=examples%2Fintroduction.ipynb
