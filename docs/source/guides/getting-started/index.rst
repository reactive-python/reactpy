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

    .. grid:: 1 2 2 2

        .. grid-item-card:: :octicon:`tools` Installing IDOM
            :link: installing-idom
            :link-type: doc

            Learn how IDOM can be installed in a variety of different ways - with
            different web servers and even in different frameworks.

        .. grid-item-card:: :octicon:`play` Running IDOM
            :link: running-idom
            :link-type: doc

            See how IDOM can be run with a variety of different production servers or be
            added to existing applications.

The fastest way to get started with IDOM is to try it out in a `Juptyer Notebook
<https://mybinder.org/v2/gh/idom-team/idom-jupyter/main?urlpath=lab/tree/notebooks/introduction.ipynb>`__.
If you want to use a Notebook to work through the examples shown in this documentation,
you'll need to replace calls to ``idom.run(App)`` with a line at the end of each cell
that constructs the ``App()`` in question. If that doesn't make sense, the introductory
notebook linked below will demonstrate how to do this:

.. card::
    :link: https://mybinder.org/v2/gh/idom-team/idom-jupyter/main?urlpath=lab/tree/notebooks/introduction.ipynb

    .. image:: _static/idom-in-jupyterlab.gif
        :scale: 72%
        :align: center


Section 1: Installing IDOM
--------------------------

The next fastest option is to install IDOM along with a supported backend (like
``starlette``) with ``pip``:

.. code-block:: bash

    pip install "idom[starlette]"

To check that everything is working you can run the sample application:

.. code-block:: bash

    python -c "import idom; idom.run(idom.sample.SampleApp)"

.. note::

    This launches a simple development server which is good enough for testing, but
    probably not what you want to use in production. When deploying in production,
    there's a number of different ways of :ref:`running IDOM <Section 2: Running IDOM>`.

You should then see a few log messages:

.. code-block:: text

    2022-03-27T11:58:59-0700 | WARNING | You are running a development server. Change this before deploying in production!
    2022-03-27T11:58:59-0700 | INFO | Running with 'Starlette' at http://127.0.0.1:8000

The second log message includes a URL indicating where you should go to view the app.
That will usually be http://127.0.0.1:8000. Once you go to that URL you should see
something like this:

.. card::

    .. idom-view:: _examples/sample_app

If you get a ``RuntimeError`` similar to the following:

.. code-block:: text

    Found none of the following builtin server implementations...

Then be sure you run ``pip install "idom[starlette]"`` instead of just ``idom``. For
anything else, report your issue in IDOM's :discussion-type:`discussion forum
<problem>`.

.. card::
    :link: installing-idom
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Learn how IDOM can be installed in a variety of different ways - with different web
    servers and even in different frameworks.


Section 2: Running IDOM
-----------------------

Once you've :ref:`installed IDOM <Installing IDOM>`, you'll want to learn how to run an
application. Throughout most of the examples in this documentation, you'll see the
:func:`~idom.backend.utils.run` function used. While it's convenient tool for
development it shouldn't be used in production settings - it's slow, and could leak
secrets through debug log messages.

.. idom:: _examples/hello_world

.. card::
    :link: running-idom
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    See how IDOM can be run with a variety of different production servers or be
    added to existing applications.
