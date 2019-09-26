Installation
============

IDOM is on PyPI_ so all you need to do is use pip_ to install a **stable** version:

.. code-block:: bash

    pip install idom

To get a **pre-release**:

.. code-block:: bash

    pip install idom --pre

.. note::

    Pre-releases may be unstable or subject to change


Development Version
-------------------

In order to work with IDOM's source code you'll need to install:

- git_

- Yarn_

You'll begin by copy the source from GitHub onto your computer using Git:

.. code-block:: bash

    git clone https://github.com/rmorshea/idom.git
    cd idom

At this point you should be able to run this install command to:

- Install an editable version of the Python code

- Transpile the Javascript and copy it to ``src/py/idom/static``

- Install some pre-commit hooks for Git

.. code-block:: bash

    pip install -e . -r requirements.txt && pre-commit install

If you modify a Javascript library you'll need to re-run this command:

.. code-block:: bash

    pip install -e .

This will transpile the Javascript again and copy it to the
``src/py/idom/static`` folder.


Running The Test
----------------

The test suite for IDOM covers:

1. Server-side Python code using PyTest_

2. The end-to-end application using Selenium_

3. (Coming soon...) Client side Javascript code

To run the full suite of tests you'll need to install:

- `Google Chrome`_

- ChromeDriver_.

.. warning::

    Be sure the version of `Google Chrome`_ and ChromeDriver_ you install are compatible.

Once you've installed the aforementined browser and web driver you should be able to
run:

.. code-block:: bash

    pytest src/py/tests

If you prefer to run the tests using a headless browser:

.. code-block:: bash

    pytest src/py/tests --headless


Experimental Python Language Extension
--------------------------------------

IDOM also provides an optional extension to the Python language with an fstring_-like
template syntax for writing HTMl.

.. code-block::
    :emphasize-lines: 7-11

    # coding=idom
    import idom

    size = "30px"
    text = "Hello!"

    model = html"""
    <div height={size} width={size} >
        <p>{text}</p>
    </div>
    """

    assert model == {
        "tagName": "div",
        "attributes": {"height": "30px", "width": "30px"},
        "children": ["\n    ", {"tagName": "p", "children": ["Hello!"]}, "\n"],
    }
    ```

.. note::

    This idea was inspired by `pyxl <https://github.com/dropbox/pyxl>`__

.. warning::

    This is an experimental feature that is subject to change


HTML Template Usage
...................

Every file that uses the HTML template syntax must:

1. Have an `html` encoding indicator as its first or second line.
2. Import `idom` into its namespace.

So your files should all start a bit like this:

```python
# coding=html
import idom
```

If you haven't :ref:`permanently installed <HTML Template Syntax Installation>` the
language extension you'll need to import modules with HTML Template Syntax, you'll need to make sure
`idom` has been imported at your application's entry point to register the language
extension before importing your module:

.. code-block::

    import idom
    import my_app

    app.run()

Where ``my_app.py`` would have the following contents:

.. code-block::

    # coding=html
    import idom

    @idom.element
    async def Hello():
        return html"<h1>Hello!</h1>"

    app = idom.server.sanic.PerClientState(Slideshow)


HTML Template Syntax Installation
.................................

If you want to more permanently install the language extension you can run the console command:

.. code-block:: bash

    idom codec register

Which can be undone (if desired) later:

.. code-block:: bash

    idom codec deregister

This is **optional**, because you can always `import idom` at the root of your application
to enable the extension. After this initial import all the follow with `coding=vdom`
will be appropriately transpiled.


Additional Support For HTML Template Syntax
...........................................

You won't be able to use the HTML template syntax directly in Python's default REPL, but
it will work out of the box with:

1. Jupyter_

2. IPython_


.. Links
.. =====

.. _Google Chrome: https://www.google.com/chrome/
.. _ChromeDriver: https://chromedriver.chromium.org/downloads
.. _git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
.. _Git Bash: https://gitforwindows.org/
.. _PyPI: https://pypi.org/project/idom
.. _pip: https://pypi.org/project/pip/
.. _PyTest: pytest <https://docs.pytest.org
.. _Selenium: https://www.seleniumhq.org/
.. _Yarn: https://yarnpkg.com/lang/en/docs/install
.. _Jupyter: https://jupyter.org
.. _IPython: http://ipython.org/
.. _fstring: https://www.python.org/dev/peps/pep-0498/
