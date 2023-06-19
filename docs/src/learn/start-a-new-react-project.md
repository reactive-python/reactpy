---
title: Start a New React Project
---

## Overview

<p class="intro" markdown>

If you want to build a new app or a new website fully with ReactPy, we recommend picking one of the ReactPy-compatible backends popular in the community. These backend frameworks provide features that most apps and sites eventually need, including routing, data fetching, and session management.

</p>


## Built-in Backends

<!-- FIXME: This is reliant on https://github.com/reactive-python/reactpy/issues/1071 -->

!!! note

    Some of our frameworks are considered _built-in_, meaning that compatibility for these backends are contained within `reactpy.backend.*`.

    In order to run ReactPy with these frameworks, you will need to run `reactpy.backend.*.configure(...)` on your ASGI application. This command will configure the necessary settings and routes for ReactPy to work properly.

    For example, this is how you would configure ReactPy for FastAPI:

	```python linenums="0"
	{% include "../../examples/python/start_a_new_react_project/configure_example.py" %}
	```

### FastAPI

FastAPI is a high-performance web framework that is designed for speed and efficiency. It is built on top of the asyncio library and uses a number of optimizations to achieve its performance. FastAPI is a good choice for web applications that need to be fast and scalable.

!!! example "Terminal"

    ```bash linenums="0"
    pip install reactpy[fastapi]
    ```

If you're new to FastAPI, check out the [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/).

You will need to [configure FastAPI](#built-in-backends) in order to use it with ReactPy.

### Flask

Flask is a microframework that is lightweight and easy to use. It is a good choice for small and simple web applications. Flask does not include many features out of the box, but it is highly customizable and can be extended with a variety of third-party libraries.

!!! example "Terminal"

    ```bash linenums="0"
    pip install reactpy[flask]
    ```

If you're new to Flask, check out the [Flask tutorial](https://flask.palletsprojects.com/en/latest/tutorial/).

You will need to [configure Flask](#built-in-backends) in order to use it with ReactPy.

### Sanic

Sanic is a microframework that is designed for speed and performance. It is built on top of the asyncio library and uses a number of optimizations to achieve its performance. Sanic is a good choice for web applications that need to be fast and scalable.

!!! example "Terminal"

    ```bash linenums="0"
    pip install reactpy[sanic]
    ```

If you're new to Sanic, check out the [Sanic tutorial](https://sanicframework.org/en/guide/).

You will need to [configure Sanic](#built-in-backends) in order to use it with ReactPy.

### Starlette

Starlette is a lightweight framework that is designed for simplicity and flexibility. It is built on top of the ASGI standard and is very easy to extend. Starlette is a good choice for web applications that need to be simple and flexible.

!!! example "Terminal"

    ```bash linenums="0"
    pip install reactpy[starlette]
    ```

If you're new to Starlette, check out the [Starlette tutorial](https://www.starlette.io/tutorial/).

You will need to [configure Starlette](#built-in-backends) in order to use it with ReactPy.

### Tornado

Tornado is a scalable web framework that is designed for high-traffic applications. It is built on top of the asyncio library and uses a number of optimizations to achieve its scalability. Tornado is a good choice for web applications that need to handle a lot of traffic.

!!! example "Terminal"

    ```bash linenums="0"
    pip install reactpy[tornado]
    ```

If you're new to Tornado, check out the [Tornado tutorial](https://www.tornadoweb.org/en/stable/guide/).

You will need to [configure Tornado](#built-in-backends) in order to use it with ReactPy.

## External Backends

### Django

[Django](https://www.djangoproject.com/) is a full-featured web framework that provides a batteries-included approach to web development. It includes features such as ORM, templating, authentication, and authorization. Django is a good choice for large and complex web applications.

!!! example "Terminal"

    ```bash linenums="0"
    pip install reactpy-django
    ```

If you're new to Django, check out the [Django tutorial](https://docs.djangoproject.com/en/dev/intro/tutorial01/).

You will need to [configure Django](https://reactive-python.github.io/reactpy-django/get-started/installation/) in order to use it with ReactPy.

### Jupyter

Jupyter is an interactive computing environment that is used for data science and machine learning. It allows users to run code, visualize data, and collaborate with others in a live environment. Jupyter is a powerful tool for data scientists and machine learning engineers.

!!! example "Terminal"

    ```bash linenums="0"
    pip install reactpy-jupyter
    ```

If you're new to Jupyter, check out the [Jupyter tutorial](https://jupyter.org/try).

You will need to [configure Jupyter](https://github.com/reactive-python/reactpy-jupyter#readme) in order to use it with ReactPy.

### Plotly Dash

Plotly Dash is a web application framework that is used to create interactive dashboards. It allows users to create dashboards that can be used to visualize data and interact with it in real time. Plotly Dash is a good choice for creating dashboards that need to be interactive and informative.

!!! example "Terminal"

    ```bash linenums="0"
    pip install reactpy-dash
    ```

If you're new to Plotly Dash, check out the [Plotly Dash tutorial](https://dash.plotly.com/installation).

You will need to [configure Plotly Dash](https://github.com/reactive-python/reactpy-dash#readme) in order to use it with ReactPy.

!!! info "Deep Dive"

    <font size="4">**Can I use ReactPy without a backend framework?**</font>

    You can not ReactPy without a backend—this project was designed to be built on-top of existing web frameworks. 

    Here's why.

    You can think of ReactPy as ReactJS server side rendering, but with a Python server. We rely on Python web frameworks and webservers in order to process ReactPy traffic. **This means that you can [use any Python web framework](../learn/creating-backends.md) as a ReactPy backend, as long as it supports the ASGI standard.** As your project grows with every new feature, you may want to switch backends in the future. As a result, we recommend keeping all backend-related logic within hook functions in order to make the "points of integration" between ReactPy and your backend as small as possible.
	
	**If you're building a new app or a site fully with ReactPy, we recommend using your favorite backend combined with [`reactpy-router`](https://github.com/reactive-python/reactpy-router) to create a Single Page Application (SPA).**
