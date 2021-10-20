Installation
============

You can install IDOM with ``pip``:

.. code-block:: bash

    pip install idom[stable]

.. note::

    Some shells may require you to inclose the install target in quotes
    (e.g. ``"idom[stable]"``)

This includes a default implementation for its :ref:`Layout Server`. You can switch to a
different one by replacing ``stable`` with one of the following other options:

- ``fastapi`` - https://fastapi.tiangolo.com
- ``flask`` - https://palletsprojects.com/p/flask/
- ``sanic`` - https://sanicframework.org
- ``tornado`` - https://www.tornadoweb.org/en/stable/

If you need to you can install more than one option by separating them with commas:

.. code-block:: bash

    pip install idom[fastapi,flask,sanic,tornado,testing]

.. note::

    If you want to integrate IDOM with `Django <https://www.djangoproject.com/>`__
    you'll need to use `django-idom <https://github.com/idom-team/django-idom>`__
    instead.

Install Test Tooling
--------------------

IDOM also provides some useful tools to ensure your applications run correctly. You
can install these with ``pip`` similarly to the server implementations above:

.. code-block:: bash

    pip install idom[testing]

This will install ``selenium`` which is useful when unit testing along with
``flake8-idom-hooks`` which is used to enforce the :ref:`Rules of Hooks`.
