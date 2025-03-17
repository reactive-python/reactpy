## Overview

<p class="intro" markdown>

If you want to add some interactivity to your existing project, you don't have to rewrite it in React. Add React to your existing stack, and render interactive React components anywhere.

</p>

## Using React for an entire subroute of your existing website

Let's say you have an existing web app at `example.com` built with another server technology (like Rails), and you want to implement all routes starting with `example.com/some-app/` fully with React.

### Using an ASGI subroute

Here's how we recommend to set it up:

1. **Build the React part of your app** using one of the [ReactPy executors](./creating-a-react-app.md).
2. **Specify `/some-app` as the _base path_** in your executors kwargs (`#!python path_prefix="/some-app"`).
3. **Configure your server or a proxy** so that all requests under `/some-app/` are handled by your React app.

This ensures the React part of your app can [benefit from the best practices](./creating-a-react-app.md) baked into those frameworks.

### Using static site generation ([SSG](https://developer.mozilla.org/en-US/docs/Glossary/SSG))

<!-- These apps can be deployed to a [CDN](https://developer.mozilla.org/en-US/docs/Glossary/CDN) or static hosting service without a server. -->

Support for SSG is coming in a [future version](https://github.com/reactive-python/reactpy/issues/1272).

## Using React for a part of your existing page

Let's say you have an existing page built with another Python web technology (ASGI or WSGI), and you want to render interactive React components somewhere on that page.

The exact approach depends on your existing page setup, so let's walk through some details.

### Using ASGI Middleware

ReactPy supports running as middleware for any existing ASGI application. ReactPy components are embedded into your existing HTML templates using Jinja2. You can use any ASGI framework, however for demonstration purposes we have selected [Starlette](https://www.starlette.io/) for the example below.

First, install ReactPy, Starlette, and your preferred ASGI webserver.

!!! example "Terminal"

    ```linenums="0"
    pip install reactpy[asgi,jinja] starlette uvicorn[standard]
    ```

Next, configure your ASGI framework to use ReactPy's Jinja2 template tag. The method for doing this will vary depending on the ASGI framework you are using. Below is an example that follow's [Starlette's documentation](https://www.starlette.io/templates/):

!!! abstract "Note"

    The `ReactPyJinja` extension enables a handful of [template tags](../reference/jinja.md) that allow you to render ReactPy components in your templates. The `component` tag is used to render a ReactPy SSR component, while the `pyscript_setup` and `pyscript_component` tags can be used together to render CSR components.

```python linenums="0" hl_lines="6 11 17"
{% include "../../examples/add_react_to_an_existing_project/asgi_configure_jinja.py" %}
```

Now you will need to wrap your existing ASGI application with ReactPy's middleware, define the dotted path to your root components, and render your components in your existing HTML templates.

=== "main.py"

    ```python hl_lines="6 22"
    {% include "../../examples/add_react_to_an_existing_project/asgi_middleware.py" %}
    ```

=== "my_components.py"

    ```python
    {% include "../../examples/add_react_to_an_existing_project/asgi_component.py" %}
    ```

=== "my_template.html"

    ```html hl_lines="5 9"
    {% include "../../examples/add_react_to_an_existing_project/asgi_template.html" %}
    ```

Finally, use your webserver of choice to start ReactPy:

!!! example "Terminal"

    ```linenums="0"
    uvicorn main:reactpy_app
    ```

### Using WSGI Middleware

Support for WSGI executors is coming in a [future version](https://github.com/reactive-python/reactpy/issues/1260).

## External Executors

!!! abstract "Note"

    **External executors** exist outside ReactPy's core library and have significantly different installation and configuration instructions.

    Make sure to follow the documentation for setting up your chosen _external_ executor.

### Django

[Django](https://www.djangoproject.com/) is a full-featured web framework that provides a batteries-included approach to web development.

Due to it's batteries-included approach, ReactPy has unique features only available to this executor.

To learn how to configure Django for ReactPy, see the [ReactPy-Django documentation](https://reactive-python.github.io/reactpy-django/).

<!--
TODO: Fix reactpy-jupyter
### Jupyter

Jupyter is an interactive computing environment that is used for data science and machine learning. It allows users to run code, visualize data, and collaborate with others in a live environment. Jupyter is a powerful tool for data scientists and machine learning engineers.

!!! example "Terminal"

    ```linenums="0"
    pip install reactpy-jupyter
    ```

If you're new to Jupyter, check out the [Jupyter tutorial](https://jupyter.org/try).

ReactPy has unique [configuration instructions](https://github.com/reactive-python/reactpy-jupyter#readme) to use Jupyter. -->

<!--
TODO: Fix reactpy-dash
### Plotly Dash

Plotly Dash is a web application framework that is used to create interactive dashboards. It allows users to create dashboards that can be used to visualize data and interact with it in real time. Plotly Dash is a good choice for creating dashboards that need to be interactive and informative.

!!! example "Terminal"

    ```linenums="0"
    pip install reactpy-dash
    ```

If you're new to Plotly Dash, check out the [Plotly Dash tutorial](https://dash.plotly.com/installation).

ReactPy has unique [configuration instructions](https://github.com/reactive-python/reactpy-dash#readme) to use Plotly Dash. -->
