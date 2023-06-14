---
hide:
    - navigation
    - toc
---

[ReactPy](https://reactpy.dev/) is a library for building user interfaces in Python without Javascript. ReactPy interfaces are made from components that look and behave similar to those found in [ReactJS](https://reactjs.org/). Designed with simplicity in mind, ReactPy can be used by those without web development experience while also being powerful enough to grow with your ambitions.

<table align="center">
    <thead>
        <tr>
            <th colspan="2" style="text-align: center">Supported Backends</th>
        <tr>
            <th style="text-align: center">Built-in</th>
            <th style="text-align: center">External</th>
        </tr>
    </thead>
    <tbody>
        <tr>
        <td>
            <a href="https://reactpy.dev/docs/guides/getting-started/installing-reactpy.html#officially-supported-servers">
                Flask, FastAPI, Sanic, Tornado
            </a>
        </td>
        <td>
            <a href="https://github.com/reactive-python/reactpy-django">Django</a>,
            <a href="https://github.com/reactive-python/reactpy-jupyter">Jupyter</a>,
            <a href="https://github.com/idom-team/idom-dash">Plotly-Dash</a>
        </td>
        </tr>
    </tbody>
</table>

# At a Glance

To get a rough idea of how to write apps in ReactPy, take a look at this tiny _Hello World_ application.

```python
from reactpy import component, html, run

@component
def hello_world():
    return html.h1("Hello, World!")

run(hello_world)
```

# Resources

Follow the links below to find out more about this project.

-   [Try ReactPy (Jupyter Notebook)](https://mybinder.org/v2/gh/reactive-python/reactpy-jupyter/main?urlpath=lab/tree/notebooks/introduction.ipynb)
-   [Documentation](https://reactpy.dev/)
-   [GitHub Discussions](https://github.com/reactive-python/reactpy/discussions)
-   [Discord](https://discord.gg/uNb5P4hA9X)
-   [Contributor Guide](https://reactpy.dev/docs/about/contributor-guide.html)
-   [Code of Conduct](https://github.com/reactive-python/reactpy/blob/main/CODE_OF_CONDUCT.md)
