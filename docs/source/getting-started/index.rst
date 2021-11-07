Getting Started
===============

.. toctree::
    :hidden:

    installing-idom
    running-idom
    testing-idom

The fastest way to get started with IDOM is to install it with ``pip``:

.. code-block:: bash

    pip install "idom[stable]"

Then, to check that everything is working you can run the sample application:

.. code-block:: bash

    python -c "import idom; idom.run_sample_app(open_browser=True)"

This should automatically open up a browser window to a page that looks like this:

.. interactive-widget:: sample_app
    :no-activate-button:
    :margin: 12

.. dropdown:: Encountered a problem?
    :animate: fade-in
    :color: warning

    If you get a ``RuntimeError`` similar to the following:

    .. code-block:: text

        Found none of the following builtin server implementations...

    Then be sure you installed ``"idom[stable]"`` and not just ``idom``.

    For anything else, report your issue in IDOM's
    `discussion forum <https://github.com/idom-team/idom/discussions/categories/help>`__.

Once you've confirmed that the sample application works as expected you can follow along
with :ref:`the lessons <Learning IDOM>` in the rest of this documentation.


Try IDOM Now!
-------------

link to binder...
