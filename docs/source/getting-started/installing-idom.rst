Installing IDOM
===============

The easiest way to ``pip`` install idom is to do so using the ``stable`` option:

.. code-block:: bash

    pip install "idom[stable]"

This includes a set of default dependencies for one of the builtin web server
implementation. If you want to install IDOM without these dependencies you may simply
``pip install idom``.


Installing Other Servers
------------------------

IDOM includes built-in support for a variety web server implementations. To install the
required dependencies for each you should substitute ``stable`` from the ``pip install``
command above with one of the options below:

- ``fastapi`` - https://fastapi.tiangolo.com
- ``flask`` - https://palletsprojects.com/p/flask/
- ``sanic`` - https://sanicframework.org
- ``tornado`` - https://www.tornadoweb.org/en/stable/

If you need to, you can install more than one option by separating them with commas:

.. code-block:: bash

    pip install idom[fastapi,flask,sanic,tornado]

Once this is complete you should be able to :ref:`run IDOM <Running IDOM>` with your
:ref:`chosen server implementation <choosing a server implementation>`.


Installing In Other Frameworks
------------------------------

While IDOM can run in a variety of contexts, sometimes web frameworks require extra work
in order to integrate with them. In these cases, the IDOM team distributes bindings for
various frameworks as separate Python packages. For documentation on how to install and
run IDOM in the supported frameworks, follow the links below:

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


Installing for Development
--------------------------

If you want to contribute to the development of IDOM or modify it, you'll want to
install a development version of IDOM. This involves cloning the repository where IDOM's
source is maintained, and setting up a :ref:`development environment`. From there you'll
be able to modifying IDOM's source code and :ref:`run its tests <Running The Tests>` to
ensure the modifications you've made are backwards compatible. If you want to add a new
feature to IDOM you should write your own test that validates its behavior.

If you have questions about how to modify IDOM or help with its development, be sure to
`start a discussion
<https://github.com/idom-team/idom/discussions/new?category=question>`__. The IDOM team
are always excited to :ref:`welcome <everyone can contribute>` new contributions and
contributors of all kinds

.. card::
    :link: /developing-idom/index
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Learn more about how to contribute to the development of IDOM.
