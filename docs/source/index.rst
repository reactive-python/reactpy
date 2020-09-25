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
    api


Try it Now!
-----------

- Using working :ref:`Examples`

- In a Jupyter Notebook - |launch-binder|


Early Days
----------

IDOM is still young. If you have ideas or find a bug, be sure to post an
`issue`_ or create a `pull request`_. Thanks in advance!


At a Glance
-----------

Let's use IDOM to create a simple slideshow which changes whenever a
user clicks an image:

.. example:: slideshow

You can try out a **Live Example** by selecting the tab and enabling the widget.

Once activated try clicking the displayed image to make it change 🖱️

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
   :target: https://mybinder.org/v2/gh/idom-team/idom-jupyter/master?filepath=notebooks%2Fintroduction.ipynb
