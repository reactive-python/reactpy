Getting Started
===============

.. toctree::
    :hidden:

    installing-idom
    running-idom

.. dropdown:: :octicon:`bookmark-fill;2em` What You'll Learn
    :color: info
    :animate: fade-in
    :open:

    .. grid:: 2

        .. grid-item-card:: :octicon:`tools` Installing IDOM
            :link: installing-idom
            :link-type: doc

            Learn how IDOM can be installed in a variety of different ways - with different web
            servers and even in different frameworks.

        .. grid-item-card:: :octicon:`play` Running IDOM
            :link: running-idom
            :link-type: doc

            See the ways that IDOM can be run with servers or be embedded in existing
            applications.

The fastest way to get started with IDOM is to try it out in a Juptyer Notebook. If you
want to use a Notebook to work through the examples shown in this documentation, you'll
want to replace calls to ``idom.run(App)`` with a line at the end of each cell that
constructs the ``App()`` in question. If that doesn't make sense, the introductory
notebook linked below will demonstrate how to do this:

.. card::
    :link: https://mybinder.org/v2/gh/idom-team/idom-jupyter/main?urlpath=lab/tree/notebooks/introduction.ipynb

    .. image:: _static/idom-in-jupyterlab.gif
        :scale: 72%
        :align: center


Section 1: Installing IDOM
--------------------------

The next fastest option is to install IDOM with ``pip``:

.. code-block:: bash

    pip install "idom[stable]"

To check that everything is working you can run the sample application:

.. code-block:: bash

    python -c "import idom; idom.run_sample_app(open_browser=True)"

This should automatically open up a browser window to a page that looks like this:

.. card::

    .. interactive-widget:: sample_app
        :activate-result:

If you get a ``RuntimeError`` similar to the following:

.. code-block:: text

    Found none of the following builtin server implementations...

Then be sure you installed ``"idom[stable]"`` and not just ``idom``.

For anything else, report your issue in IDOM's
`discussion forum <https://github.com/idom-team/idom/discussions/categories/help>`__.

.. card::
    :link: installing-idom
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Learn how IDOM can be installed in a variety of different ways - with different web
    servers and even in different frameworks.


Section 2: Running IDOM
-----------------------

Once you've :ref:`installed IDOM <Installing IDOM>`. The simplest way to run IDOM is
with the :func:`~idom.server.prefab.run` function. By default this will execute your
application using one of the builtin server implementations whose dependencies have all
been installed. Running a tiny "hello world" application just requires the following
code:

.. example:: hello_world
    :activate-result:

.. card::
    :link: running-idom
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    See the ways that IDOM can be run with servers or be embedded in existing
    applications.
