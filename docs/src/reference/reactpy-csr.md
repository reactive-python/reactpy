## Overview

<p class="intro" markdown>

`ReactPyCsr` serves a page that runs your component code **in the browser** via [PyScript](https://pyscript.net/). There is no websocket: the component renders entirely client-side.

</p>

```python linenums="0"
from reactpy.executors.asgi import ReactPyCsr

my_app = ReactPyCsr("root.py", initial="Loading...")
```

---

## Reference

### `ReactPyCsr(*file_paths, **settings)`

```python linenums="0"
from reactpy.executors.asgi import ReactPyCsr
```

#### Parameters

-   **`*file_paths`**: One or more paths to Python files containing components. Their **source is inlined into the served HTML**. Accepts `#!python str` or `#!python pathlib.Path`.

    Read once, then cached for the life of the process: `executors/pyscript/utils.py`, `fetch_cached_python_file` is decorated with `#!python functools.cache`, keyed on the path. Editing the file does not change the page on reload — restart the server. The same cache strips comments and docstrings before inlining (see [Jinja](./jinja.md#pyscript_component-tag)), so what reaches the browser is not quite what you wrote.

-   **`root_name`** *(optional)*: The name of the root component inside your Python file. Defaults to `#!python "root"`. The file may define any number of components; this one is mounted.

    ```python linenums="0"
    ReactPyCsr("components.py", root_name="my_app")
    ```

    The name must match exactly, and the object must be a component.

-   **`initial`** *(optional)*: Content shown while PyScript boots. A string or a `#!python VdomDict`. Defaults to `#!python ""`.

-   **`extra_py`** *(optional)*: Additional Python packages to install into the PyScript runtime, as version specifier strings.

-   **`extra_js`** *(optional)*: Additional JavaScript modules, as a `#!python dict[str, str]` where each **key is the URL** of the JavaScript file and the **value is the name** to export it as — `#!python {"/static/foo.js": "foo"}`. The name is how the module is reached from the component, via `#!python pyscript.js_modules.foo`. Same direction as the `#!python js_modules.main` block PyScript itself consumes.

-   **`pyscript_config`** *(optional)*: Raw PyScript configuration dictionary.

-   **`http_headers`**, **`html_head`**, **`prepend_body`**, **`html_lang`**: Same meaning as in [`ReactPy`](./reactpy.md).

-   **`**settings`**: Any key from `#!python ReactPyConfig`.

#### Returns

An ASGI application.

---

## Usage

### Files

Two files: the ASGI app, and the root component.

=== "main.py"

    ```python
    {% include "../../examples/reference_reactpy_csr/csr/main.py" start="# start" %}
    ```

=== "root.py"

    ```python
    {% include "../../examples/reference_reactpy_csr/csr_root/root.py" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Serve with `#!python uvicorn main:my_app`. The served page carries the `#!python Loading...` placeholder, the PyScript bootstrap, and your component source.

!!! warning "Your component source is public"

    `ReactPyCsr` embeds the text of every file you pass into the HTML response, so the browser can execute it. Verified: requesting the index route returned the full body of the component file, including components that are *not* mounted.

    Treat these files as client-side code. Do not read secrets, query a database, or call privileged APIs from a CSR component — anything reachable from that file is reachable by anyone who loads the page. CSR is for genuinely client-side work: offline apps, demos, UI that needs no server authority. For anything that touches data you do not publish, use [`ReactPy`](./reactpy.md) or [`ReactPyMiddleware`](./reactpy-middleware.md), which keep your Python on the server.

### How it loads

The page ReactPy generates does three things:

1. Links PyScript's CSS and module script from `{path_prefix}static/`.
2. Declares what PyScript should fetch: a `#!python packages` list for Python — ReactPy's own wheel from `{path_prefix}static/wheels/` and `#!python jsonpointer==3.*` — and a separate `#!python js_modules` entry for `#!python morphdom`, served from `{path_prefix}static/morphdom/morphdom-esm.js`. They are different lists with different installers; `#!python morphdom` is not a `#!python packages` entry.
3. Inlines your Python, then runs it under PyScript.

Verified against a running server: the initial response carries the PyScript `#!python core.js`, `"packages": ["/reactpy/static/wheels/reactpy-2.0.0b13-py3-none-any.whl", "jsonpointer==3.*"]`, `"js_modules": {"main": {"/reactpy/static/morphdom/morphdom-esm.js": "morphdom"}}`, and the `#!python initial` placeholder inside a `#!python <div class="pyscript">`. `#!python pyscript_config` lets you replace either list.

!!! info "The first load is slow"

    The browser downloads and installs a CPython runtime plus your packages before anything renders. That is what `#!python initial` is for. `#!python pyscript_config` and `#!python extra_py` let you pin packages, and `#!python packages_cache` controls re-download, but the cold start is inherent to running Python in the browser.

### Choosing CSR over the other executors

| | Where your Python runs | Needs a websocket | Source visible to the client |
| --- | --- | --- | --- |
| [`ReactPy`](./reactpy.md) | server | yes | no |
| [`ReactPyMiddleware`](./reactpy-middleware.md) | server | yes | no |
| `ReactPyCsr` | **browser** | no | **yes** |

Pick CSR when the client must work without a server connection. Pick one of the others whenever the component touches anything you would not publish.

!!! tip "PyScript without CSR"

    `#!python ReactPy` accepts `#!python pyscript_setup=True` to load PyScript alongside server-rendered components, for mixed setups. `ReactPyCsr` is the fully client-side case.

## Related

-   [Creating a Standalone React App](../learn/creating-a-react-app.md)
-   [Adding ReactPy to an Existing Project](../learn/add-react-to-an-existing-project.md) — the Jinja template tags include a CSR variant.
