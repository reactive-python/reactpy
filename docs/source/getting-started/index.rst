Getting Started
===============

.. toctree::
    :hidden:

    installing-idom
    running-idom

The fastest way to get started with IDOM is to try it out in a Juptyer Notebook:

.. card::
    :link: https://mybinder.org/v2/gh/idom-team/idom-jupyter/main?urlpath=lab/tree/notebooks/introduction.ipynb

    .. image:: /_static/idom-in-jupyterlab.gif


Quick Install
-------------

The next fastest option is to install IDOM with ``pip``:

.. code-block:: bash

    pip install "idom[stable]"

To check that everything is working you can run the sample application:

.. code-block:: bash

    python -c "import idom; idom.run_sample_app(open_browser=True)"

This should automatically open up a browser window to a page that looks like this:

.. interactive-widget:: sample_app
    :no-activate-button:
    :margin: 12

.. dropdown:: Encountered a problem?
    :animate: fade-in

    If you get a ``RuntimeError`` similar to the following:

    .. code-block:: text

        Found none of the following builtin server implementations...

    Then be sure you installed ``"idom[stable]"`` and not just ``idom``.

    For anything else, report your issue in IDOM's
    `discussion forum <https://github.com/idom-team/idom/discussions/categories/help>`__.

.. grid:: 2
    :gutter: 1

    .. grid-item-card:: :octicon:`tools` Installation Details
        :link: installing-idom
        :link-type: doc

        Learn more about the different ways to install and configure IDOM

    .. grid-item-card:: :octicon:`play` Running IDOM
        :link: running-idom
        :link-type: doc

        See how to run IDOM with different servers or make a custom server
        implementation

    .. grid-item-card:: :octicon:`rocket` Creating Interfaces
        :link: ../creating-interfaces/index
        :link-type: doc

        Discover how to create interactive applications with IDOM!

    .. grid-item-card:: :octicon:`people` Discussion Forum
        :link: https://github.com/idom-team/idom/discussions

        Report issues, ask questions, share ideas, or show projects
