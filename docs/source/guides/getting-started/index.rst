Getting Started
===============

.. toctree::
    :hidden:

    installing-reactpy
    running-reactpy

.. dropdown:: :octicon:`bookmark-fill;2em` What You'll Learn
    :color: info
    :animate: fade-in
    :open:

    .. grid:: 1 2 2 2

        .. grid-item-card:: :octicon:`tools` Installing ReactPy
            :link: installing-reactpy
            :link-type: doc

            Learn how ReactPy can be installed in a variety of different ways - with
            different web servers and even in different frameworks.

        .. grid-item-card:: :octicon:`play` Running ReactPy
            :link: running-reactpy
            :link-type: doc

            See how ReactPy can be run with a variety of different production servers or be
            added to existing applications.

The fastest way to get started with ReactPy is to try it out in a `Juptyer Notebook
<https://mybinder.org/v2/gh/reactive-python/reactpy-jupyter/main?urlpath=lab/tree/notebooks/introduction.ipynb>`__.
If you want to use a Notebook to work through the examples shown in this documentation,
you'll need to replace calls to ``reactpy.run(App)`` with a line at the end of each cell
that constructs the ``App()`` in question. If that doesn't make sense, the introductory
notebook linked below will demonstrate how to do this:

.. card::
    :link: https://mybinder.org/v2/gh/reactive-python/reactpy-jupyter/main?urlpath=lab/tree/notebooks/introduction.ipynb

    .. image:: _static/reactpy-in-jupyterlab.gif
        :scale: 72%
        :align: center


Section 1: Installing ReactPy
-----------------------------

The next fastest option is to install ReactPy along with a supported server (like
``starlette``) with ``pip``:

.. code-block:: bash

    pip install "reactpy[starlette]"

To check that everything is working you can run the sample application:

.. code-block:: bash

    python -c "import reactpy; reactpy.run(reactpy.sample.SampleApp)"

.. note::

    This launches a simple development server which is good enough for testing, but
    probably not what you want to use in production. When deploying in production,
    there's a number of different ways of :ref:`running ReactPy <Section 2: Running ReactPy>`.

You should then see a few log messages:

.. code-block:: text

    2022-03-27T11:58:59-0700 | WARNING | You are running a development server. Change this before deploying in production!
    2022-03-27T11:58:59-0700 | INFO | Running with 'Starlette' at http://127.0.0.1:8000

The second log message includes a URL indicating where you should go to view the app.
That will usually be http://127.0.0.1:8000. Once you go to that URL you should see
something like this:

.. card::

    .. reactpy-view:: _examples/sample_app

If you get a ``RuntimeError`` similar to the following:

.. code-block:: text

    Found none of the following builtin server implementations...

Then be sure you run ``pip install "reactpy[starlette]"`` instead of just ``reactpy``. For
anything else, report your issue in ReactPy's :discussion-type:`discussion forum
<problem>`.

.. card::
    :link: installing-reactpy
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Learn how ReactPy can be installed in a variety of different ways - with different web
    servers and even in different frameworks.


Section 2: Running ReactPy
--------------------------

Once you've :ref:`installed ReactPy <Installing ReactPy>`, you'll want to learn how to run an
application. Throughout most of the examples in this documentation, you'll see the
:func:`~reactpy.backend.utils.run` function used. While it's convenient tool for
development it shouldn't be used in production settings - it's slow, and could leak
secrets through debug log messages.

.. reactpy:: _examples/hello_world

.. card::
    :link: running-reactpy
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    See how ReactPy can be run with a variety of different production servers or be
    added to existing applications.
