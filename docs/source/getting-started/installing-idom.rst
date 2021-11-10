Installing IDOM
===============

The easiest way to ``pip`` install idom is to do so using the ``stable`` option:

.. code-block:: bash

    pip install "idom[stable]"

This includes a set of default dependencies for one of the builtin web server
implementation.


Installing Other Servers
------------------------

If you want to install IDOM without these dependencies you may simply ``pip install
idom`` or, alternatively, if you want a specific web server implementation you can
select on of the other installation options below:

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

While IDOM can run in a variety of contexts, sometimes web frameworks require extra work
in orer to integrate with them. In these cases, the IDOM team distributes bindings for
these frameworks as separate Python packages. For documentation on how to install and
use these, follow the links below:

.. raw:: html

    <style>
        .card-logo-image {
            display: flex;
            justify-content: center;
            align-content: center;
            padding: 10px;
            background-color: var(--color-background-primary);
            border: 2px solid var(--color-background-border);
        }
    </style>

.. grid:: 3

    .. grid-item-card::
        :link: https://github.com/idom-team/django-idom
        :img-background: _static/logo-django.svg
        :class-card: card-logo-image

    .. grid-item-card::
        :link: https://github.com/idom-team/idom-jupyter
        :img-background: _static/logo-jupyter.svg
        :class-card: card-logo-image

    .. grid-item-card::
        :link: https://github.com/idom-team/idom-dash
        :img-background: _static/logo-plotly.svg
        :class-card: card-logo-image
