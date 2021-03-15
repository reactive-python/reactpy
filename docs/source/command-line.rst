Command-line
============

IDOM supplies a CLI for:

- Displaying version information
- Installing Javascript packages
- Restoring IDOM's client


Show Version Info
-----------------

To see the version of ``idom`` being run:

.. code-block:: bash

    idom version

You can also show all available versioning information:

.. code-block:: bash

    idom version --verbose

This is useful for bug reports.


Install Javascript Packages
---------------------------

You can install Javascript packages at the command line rather than doing it
:ref:`programmatically <Dynamically Install Javascript>`:

.. code-block:: bash

    idom install some-js-package versioned-js-package@^1.0.0

If the package is already installed then the build will be skipped.


Restore The Client
------------------

Replace IDOM's client with a backup from its original installation.

.. code-block:: bash

    idom restore

This is useful if a build of the client fails and leaves it in an unusable state.
