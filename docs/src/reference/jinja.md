## Overview

<p class="intro" markdown>

`ReactPyJinja` adds three tags to a Jinja2 environment so an existing Python web app can mount ReactPy components inside templates it already owns — one tag for server-rendered components, two for components that run in the browser via PyScript.

</p>

```jinja linenums="0"
{% component "my_app.pages.counter" %}
```

Install the extra the extension needs:

```bash linenums="0"
pip install "reactpy[asgi,jinja]"
```

It lives at `reactpy.templatetags.ReactPyJinja`. Despite the `templatetags` name it is not a Django app — it is a [jinja2-simple-tags](https://pypi.org/project/jinja2-simple-tags/) `StandaloneTag`, so it works with any Jinja2 environment.

---

## Reference

### Registering the extension { #registering }

Two equivalent forms:

```python linenums="0"
from jinja2 import Environment, FileSystemLoader

from reactpy.templatetags import ReactPyJinja

# at construction
env = Environment(loader=FileSystemLoader("templates"), extensions=[ReactPyJinja])

# or afterwards
env = Environment(loader=FileSystemLoader("templates"))
env.add_extension(ReactPyJinja)
```

Both register all three tags at once; there is no way to register one alone, and no configuration to pass. Registering `ReactPyJinja(...)` as an instance and calling `#!python .register()` does **not** work — that object has no `register` method.

!!! warning "Register before a template is compiled"
    Tags are resolved when a template is *parsed*. If the environment has already compiled a template that uses them, you get `#!python jinja2.exceptions.TemplateSyntaxError: Encountered unknown tag 'component'.` Frameworks that cache templates at startup make this a startup-time error, which is easy to attribute to something else.

### `{% component "dotted.path" %}` { #component-tag }

Emits the markup that mounts a **server-side** component: an empty mount element, an import-map fallback, and a module script that calls `#!python mountReactPy`.

```jinja linenums="0"
{% component "my_app.pages.counter" %}
{% component "my_app.pages.badge", class="badge" %}
```

- **The dotted path** *(required)*: the import path of the root component function — the same string you give `#!python ReactPyMiddleware`'s `#!python root_components`. It is embedded verbatim into the emitted JavaScript; ReactPy imports it on the server when the browser asks to connect.
- **`class`** *(optional)*: a CSS class for the generated mount element, producing `#!html <div id="..." class="badge"></div>`.

`#!python safe_output` is set on the tag, so Jinja does not escape the returned HTML even under `#!python autoescape=True`.

!!! warning "Arguments are parsed as Python expressions"
    The tag uses Jinja's argument parser, so keyword arguments must follow a comma — `#!python {% component "m.f" class="x" %}` fails at template-compile time with `#!python TemplateSyntaxError: expected token ',', got 'class'`. Write `#!python {% component "m.f", class="x" %}`.

    The path may be a quoted string (as above) or a Jinja expression that resolves to one; in the latter case it is read from the template context, so an unquoted `#!python my_app.pages.counter` requires `#!python my_app` to be a context variable.

#### Errors this tag raises

| Mistake | Error |
| --- | --- |
| Omitting the path | `#!python TypeError: component() missing 1 required positional argument: 'dotted_path'` |
| Passing a second positional | `#!python TypeError: component() takes 1 positional argument but 2 were given` |
| Any other keyword | `#!python ValueError: Unexpected keyword arguments: id, style` |
| A typo in the tag name | `#!python TemplateSyntaxError: Encountered unknown tag 'bogus_tag'.` |

A **wrong** dotted path is not one of them. Nothing checks that the module or attribute exists: the tag happily emits markup pointing at a path that will never connect, and the only symptom is a permanently empty element plus a failed request in the browser console. Verify the path against what you passed to `#!python root_components`.

### `{% pyscript_setup %}` { #pyscript-setup }

Emits the PyScript bootstrap — stylesheet, module script, and the config that installs ReactPy into the browser.

```jinja linenums="0"
<head>
    {% pyscript_setup %}
</head>
```

- **`extra_py`** *(optional, positional, repeatable)*: extra Python packages for the PyScript runtime — `#!python {% pyscript_setup "numpy", "rich" %}`. They are appended to the package list alongside ReactPy's own wheel.
- **`extra_js`** *(optional, keyword)*: a **JSON object** mapping module URLs to names, e.g. `#!python extra_js='{"./my.js": "mylib"}'`. It is merged into the config's `#!python js_modules.main`. A plain string that is not valid JSON raises `#!python json.decoder.JSONDecodeError`.
- **`config`** *(optional, keyword)*: a JSON object (or JSON string) merged over the generated config, letting you set anything PyScript accepts.

Put this tag in the document head, **once**. A page with several `#!python pyscript_component` tags needs one bootstrap, not one per component.

!!! info "Packages install in the browser"
    Anything in `#!python extra_py` must be installable under Pyodide — pure Python, or a wheel built for it. A package with C extensions that installs cleanly on the server will fail in the browser, and the failure appears only in the browser console.

### `{% pyscript_component "path/to/file.py" %}` { #pyscript-component-tag }

Emits a `#!html <div>` plus a `#!html <script type='py'>` that runs the named file's component **in the browser**.

```jinja linenums="0"
{% pyscript_component "components/counter.py" initial="Loading..." %}
```

- **File paths** *(required, positional, repeatable)*: paths to Python files, resolved relative to the process's **current working directory** at template-render time. Several files may be passed; they are concatenated into one script.
- **`initial`** *(optional)*: markup rendered inside the mount element while PyScript boots.
- **`root`** *(optional)*: the name of the root component function, default `#!python "root"`.

Because the files are read and inlined, the browser never fetches them and your app serves no route for them.

!!! danger "The file's source ships to the client"
    The whole file — code, comments, docstrings, every string literal — is embedded in the HTML. Never read a secret into one of these files at render time, and do not use this tag for code you would not publish. This is unrelated to debug mode: turning `#!python reactpy.config.REACTPY_DEBUG` off hides nothing here.

| Mistake | Error |
| --- | --- |
| File does not exist (wrong cwd or path) | `#!python FileNotFoundError: [Errno 2] No such file or directory: 'components/missing.py'` |
| No `#!python root` function in the file | `#!python ValueError: Could not find the root component function 'root' in your PyScript file(s).` |

Both are raised at render time, so they surface as a 500 on the page — not as a broken widget.

!!! tip "Prefer `ReactPyCsr` unless you are embedding"
    For a page built from scratch, `#!python ReactPyCsr` is an ASGI app with its own URL and handles the setup tag for you. These two tags exist for putting a component inside a template you do not control. See [ReactPyCsr](reactpy-csr.md).

---

## Usage

### A server-rendered component in an existing page

=== "main.py"

    ```python
    {% include "../../examples/reference_jinja/component_tag/main.py" start="# start" %}
    ```

=== "home.html"

    ```html
    {% include "../../examples/reference_jinja/component_tag/home.html" %}
    ```

=== "pages.py"

    ```python
    {% include "../../examples/reference_jinja/component_tag/pages.py" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The components cannot live in `#!python main.py` even though that is where the wiring is. The browser reaches them by dotted path, so they must sit in a module the server can import — a component defined next to the view is reachable as `#!python main.counter`, but then the template has to say exactly that. Whatever you choose, the path in `{% component %}` and the entry in `#!python root_components` must agree character for character. Nothing checks it for you: a mismatch emits markup that mounts an element which stays empty forever, and the failed import surfaces only as a server-side traceback on the websocket request.

### A client-side component

Setup in the head, the component where it belongs:

=== "home.html"

    ```html
    <!doctype html>
    <html lang="en">
      <head>
        <title>Counter</title>
        {% pyscript_setup %}
      </head>
      <body>
        {% pyscript_component "components/counter.py" initial="Loading..." %}
      </body>
    </html>
    ```

=== "counter.py"

    ```python
    {% include "../../examples/reference_jinja/pyscript_component/counter.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

There is no websocket, so `#!python use_connection`, `#!python use_scope`, and `#!python use_location` have no connection to read and raise — see [Use Connection](use-connection.md).

### Which one to use

| | `#!python {% component %}` | `#!python {% pyscript_setup %}` + `#!python {% pyscript_component %}` |
| --- | --- | --- |
| Component runs | Server | Browser |
| Needs a websocket | Yes | No |
| Component source visible to users | No | **Yes** |
| First paint | Server HTML, then it connects | `#!python initial` until PyScript boots |
| Can read the request | Yes (`use_connection`, `use_scope`, `use_location`) | No |
| Needs a route on your app | Yes | No |
| Packages must be Pyodide-compatible | No | Yes |

## Related

-   [Add React to an Existing Project](../learn/add-react-to-an-existing-project.md) — the full Starlette wiring these tags are for
-   [ReactPyMiddleware](reactpy-middleware.md) — the middleware that serves server-rendered components, and the markup this tag generates
-   [ReactPyCsr](reactpy-csr.md) — the ASGI-app form of the PyScript tags
-   [ReactPy](reactpy.md) — standalone server-rendered app
-   [Common Props](common-props.md) — what a component may return
