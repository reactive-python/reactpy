## Overview

<p class="intro" markdown>

If you want to build a new app or website with React, we recommend starting with a standalone executor.

</p>

If your app has constraints not well-served by existing web frameworks, you prefer to build your own framework, or you just want to learn the basics of a React app, you can use ReactPy in **standalone mode**.

## Using ReactPy for full-stack

ReactPy is a component library that helps you build a full-stack web application. For convenience, ReactPy is also bundled with several different standalone executors.

These standalone executors are the easiest way to get started with ReactPy, as they require no additional setup or configuration.

!!! abstract "Note"

    **Standalone ReactPy requires a server**

    In order to serve the initial HTML page, you will need to run a server. The ASGI examples below use [Uvicorn](https://www.uvicorn.org/), but you can use [any ASGI server](https://github.com/florimondmanca/awesome-asgi#servers).

    Executors on this page can either support client-side rendering ([CSR](https://developer.mozilla.org/en-US/docs/Glossary/CSR)) or server-side rendering ([SSR](https://developer.mozilla.org/en-US/docs/Glossary/SSR))

### Running via ASGI SSR

ReactPy can run in **server-side standalone mode**, where both page loading and component rendering occurs on an ASGI server.

This executor is the most commonly used, as it provides maximum extensibility.

First, install ReactPy and your preferred ASGI webserver.

!!! example "Terminal"

    ```linenums="0"
    pip install reactpy[asgi] uvicorn[standard]
    ```

Next, create a new file called `main.py` containing the ASGI application:

=== "main.py"

    ```python
    {% include "../../examples/creating_a_react_app/asgi_ssr.py" %}
    ```

Finally, use your webserver of choice to start ReactPy:

!!! example "Terminal"

    ```linenums="0"
    uvicorn main:my_app
    ```

### Running via ASGI CSR

ReactPy can run in **client-side standalone mode**, where the initial page is served using the ASGI protocol. This is configuration allows direct execution of Javascript, but requires special considerations since all ReactPy component code is run on the browser [via WebAssembly](https://pyscript.net/).

First, install ReactPy and your preferred ASGI webserver.

!!! example "Terminal"

    ```linenums="0"
    pip install reactpy[asgi] uvicorn[standard]
    ```

Next, create a new file called `main.py` containing the ASGI application, and a `root.py` file containing the root component:

=== "main.py"

    ```python
    {% include "../../examples/creating_a_react_app/asgi_csr.py" %}
    ```

=== "root.py"

    ```python
    {% include "../../examples/creating_a_react_app/asgi_csr_root.py" %}
    ```

Finally, use your webserver of choice to start ReactPy:

!!! example "Terminal"

    ```linenums="0"
    uvicorn main:my_app
    ```

### Running via WSGI SSR

Support for WSGI executors is coming in a [future version](https://github.com/reactive-python/reactpy/issues/1260).

### Running via WSGI CSR

Support for WSGI executors is coming in a [future version](https://github.com/reactive-python/reactpy/issues/1260).
