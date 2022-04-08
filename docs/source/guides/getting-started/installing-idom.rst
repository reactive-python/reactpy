Installing IDOM
===============

Installing IDOM with ``pip`` will typically require doing so alongside a built-in
backend implementation. This can be done by specifying an installation extra using
square brackets. For example, if we want to run IDOM using the `Starlette
<https://www.starlette.io/>`__ backend we would run:

.. code-block:: bash

    pip install "idom[starlette]"

If you want to install a "pure" version of IDOM without a backend implementation you can
do so without any installation extras. You might do this if you wanted to use a backend
which does not have built-in support or if you wanted to manually pin your dependencies:

.. code-block:: bash

    pip install idom


Built-in Backends
-----------------

IDOM includes built-in support for a variety backend implementations. To install the
required dependencies for each you should substitute ``starlette`` from the ``pip
install`` command above with one of the options below:

- ``fastapi`` - https://fastapi.tiangolo.com
- ``flask`` - https://palletsprojects.com/p/flask/
- ``sanic`` - https://sanicframework.org
- ``starlette`` - https://www.starlette.io/
- ``tornado`` - https://www.tornadoweb.org/en/stable/

If you need to, you can install more than one option by separating them with commas:

.. code-block:: bash

    pip install "idom[fastapi,flask,sanic,starlette,tornado]"

Once this is complete you should be able to :ref:`run IDOM <Running IDOM>` with your
chosen implementation.


Other Backends
--------------

While IDOM can run in a variety of contexts, sometimes frameworks require extra work in
order to integrate with them. In these cases, the IDOM team distributes bindings for
those frameworks as separate Python packages. For documentation on how to install and
run IDOM in these supported frameworks, follow the links below:

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

        .transparent-text-color {
            color: transparent;
        }
    </style>

.. role:: transparent-text-color

.. We add transparent-text-color to the text so it's not visible, but it's still
.. searchable.

.. grid:: 3

    .. grid-item-card::
        :link: https://github.com/idom-team/django-idom
        :img-background: _static/logo-django.svg
        :class-card: card-logo-image

        :transparent-text-color:`Django`

    .. grid-item-card::
        :link: https://github.com/idom-team/idom-jupyter
        :img-background: _static/logo-jupyter.svg
        :class-card: card-logo-image

        :transparent-text-color:`Jupyter`

    .. grid-item-card::
        :link: https://github.com/idom-team/idom-dash
        :img-background: _static/logo-plotly.svg
        :class-card: card-logo-image

        :transparent-text-color:`Plotly Dash`


For Development
---------------

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
    :link: /about/contributor-guide
    :link-type: doc

    :octicon:`book` Read More
    ^^^^^^^^^^^^^^^^^^^^^^^^^

    Learn more about how to contribute to the development of IDOM.
