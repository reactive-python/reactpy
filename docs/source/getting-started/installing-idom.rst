Installing IDOM
===============

The simplest way to install idom is to do so using the ``stable`` option:

.. code-block:: bash

    pip install "idom[stable]"

This includes a set of default dependencies that will support a builtin web server
implementation. If you want to install IDOM without these dependencies you may simply
``pip install idom`` or, alternatively, if you want a specific web server implementation
you can select on of the other installation options below:

- ``fastapi`` - https://fastapi.tiangolo.com
- ``flask`` - https://palletsprojects.com/p/flask/
- ``sanic`` - https://sanicframework.org
- ``tornado`` - https://www.tornadoweb.org/en/stable/

If you need to, you can install more than one option by separating them with commas:

.. code-block:: bash

    pip install idom[fastapi,flask,sanic,tornado]

Once this is complete you should be able to :ref:`run IDOM applications <Running IDOM>`.


Installing In Other Frameworks
------------------------------

IDOM can be run in a variety of contexts. These tend to be supported through the
installation of additional Python packages. We briefly discuss how to
:ref:`run IDOM in other frameworks <Running In Other Frameworks>`, but for specific
information, you should refer to the specific documentation for the each Required
Package that's been linked below:

.. list-table::
    :header-rows: 1
    :align: center
    :widths: auto

    * - Framework
      - Required Package

    * - `Django <https://docs.djangoproject.com/en/3.2/>`__
      - `django-idom <https://github.com/idom-team/django-idom>`__

    * - `Jupyter <https://jupyter.readthedocs.io/en/latest/>`__
      - `idom-jupyter <https://github.com/idom-team/idom-jupyter>`__

    * - `Plotly Dash <https://dash.plotly.com/>`__
      - `idom-dash <https://github.com/idom-team/idom-dash>`__
