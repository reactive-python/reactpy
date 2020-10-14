IDOM
====

Libraries for defining and controlling interactive webpages with Python
3.7 and above.

.. toctree::
    :hidden:
    :caption: User Guide

    installation
    getting-started
    life-cycle-hooks
    core-concepts
    custom-javascript
    examples

.. toctree::
    :hidden:
    :caption: Reference

    GitHub <https://github.com/idom-team/idom>
    package-api
    specifications
    extra-features


Early Days
----------

IDOM is still young. Be sure to post any `issues`_ you have or contribute by creating a
`pull request`_.


At a Glance
-----------

Let's use IDOM to create a simple slideshow which changes whenever a
user clicks an image:

.. example:: slideshow

Try selecting the "Live Example" tab in the view above and enabling the widget.

Once activated try clicking the displayed image to make it change 🖱️

.. note::

    You can display the same thing in a Jupyter Notebook by installing ``idom-jupyter``:

    .. code-block:: bash

        pip install idom-jupyter

    And replacing ``idom.run`` with ``idom_jupyter.run``:

    .. code-block::

        import idom_jupyter
        idom_jupyter.run(Slideshow)

    Try it out on Binder now: |launch-binder|


.. Links
.. =====

.. _issues: https://github.com/rmorshea/idom/issues
.. _pull request: https://github.com/rmorshea/idom/pulls
.. _IDOM Sandbox: https://idom-sandbox.herokuapp.com
.. |launch-binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/idom-team/idom-jupyter/main?filepath=notebooks%2Fintroduction.ipynb
