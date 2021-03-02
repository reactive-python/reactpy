Specifications
==============

Describes various data structures and protocols used to define and communicate virtual
document object models (:ref:`VDOM <VDOM Mimetype>`). The definitions to below follow in
the footsteps of
`a specification <https://github.com/nteract/vdom/blob/master/docs/mimetype-spec.md>`_
created by `Nteract <https://nteract.io>`_ and which was built into
`JupyterLab <https://jupyterlab.readthedocs.io/en/stable/>`_. While IDOM's specification
for VDOM is fairly well established, it should not be relied until it's been fully
adopted by the aforementioned organizations.


VDOM Mimetype
-------------

A set of definitions that explain how IDOM creates a virtual representation of
the document object model. We'll begin by looking at a bit of HTML that we'll convert
into its VDOM representation:

.. code-block:: html

    <div>
      Put your name here:
      <input
        type="text"
        minlength="4"
        maxlength="8"
        onchange="a_python_callback(event)"
      />
    </div>

.. note::

  For context, the following Python code would generate the HTML above:

  .. code-block:: python

      import idom

      async def a_python_callback(new):
          ...

      name_input_view = idom.html.div(
          idom.html.input(
              {
                  "type": "text",
                  "minLength": 4,
                  "maxLength": 8,
                  "onChange": a_python_callback,
              }
          ),
          ["Put your name here: "],
      )

We'll take this step by step in order to show exactly where each piece of the VDOM
model comes from. To get started we'll convert the outer ``<div/>``:

.. code-block:: python

    {
        "tagName": "div",
        "children": [
            "To perform an action",
            ...
        ],
        "attributes": {},
        "eventHandlers": {}
    }

.. note::

    As we move though our conversation we'll be using ``...`` to fill in places that we
    haven't converted yet.

In this simple case, all we've done is take the name of the HTML element (``div`` in
this case) and inserted it into the ``tagName`` field of a dictionary. Then we've taken
the inner HTML and added to a list of children where the text ``"to perform an action"``
has been made into a string, and the inner ``input`` (yet to be converted) will be
expanded out into its own VDOM representation. Since the outer ``div`` is pretty simple
there aren't any ``attributes`` or ``eventHandlers``.

No we come to the inner ``input``. If we expand this out now we'll get the following:

.. code-block:: python

    {
        "tagName": "div",
        "children": [
            "To perform an action",
            {
                "tagName": "input",
                "children": [],
                "attributes": {
                    "type": "text",
                    "minLength": 4,
                    "maxLength": 8
                },
                "eventHandlers": ...
            }
        ],
        "attributes": {},
        "eventHandlers": {}
    }

Here we've had to add some attributes to our VDOM. Take note of the differing
capitalization - instead of using all lowercase (an HTML convention) we've used
`camelCase <https://en.wikipedia.org/wiki/Camel_case>`_ which is very common
in JavaScript.

Last, but not least we come to the ``eventHandlers`` for the ``input``:

.. code-block:: python

    {
        "tagName": "div",
        "children": [
            "To perform an action",
            {
                "tagName": "input",
                "children": [],
                "attributes": {
                    "type": "text",
                    "minLength": 4,
                    "maxLength": 8
                },
                "eventHandlers": {
                    "onChange": {
                      "target": "unique-id-of-a_python_callback",
                      "preventDefault": False,
                      "stopPropagation": False
                    }
                }
            }
        ],
        "attributes": {},
        "eventHandlers": {}
    }

Again we've changed the all lowercase ``onchange`` into a cameCase ``onChange`` event
type name. The various properties for the ``onChange`` handler are:

- ``target``: the unique ID for a Python callback that exists in the backend.

- ``preventDefault``: Stop the event's default action. More info
  `here <https://developer.mozilla.org/en-US/docs/Web/API/Event/preventDefault>`__.

- ``stopPropagration``: prevent the event from bubbling up through the DOM. More info
  `here <https://developer.mozilla.org/en-US/docs/Web/API/Event/stopPropagation>`__.


To clearly describe the VDOM schema we've created a `JSON Schema <https://json-schema.org/>`_:

.. literalinclude:: ./vdom-json-schema.json
   :language: json


JSON Patch
----------

Updates to VDOM modules are sent using the `JSON Patch`_ specification.

... this section is still under construction :)


.. Links
.. =====
.. _JSON Patch: http://jsonpatch.com/
