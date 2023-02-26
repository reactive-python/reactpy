<img src="https://raw.githubusercontent.com/reactive-python/reactpy/main/branding/reactpy-logo-wide.svg" alt="ReactPy Logo" id="reactpy" width="500px" />

ReactPy is a library for building user interfaces in Python without Javascript. ReactPy
interfaces are made from components which look and behave similarly to this found in
[ReactJS](https://reactjs.org/). Designed with simplicity in mind, ReactPy can be used
by those without web development experience while also being powerful enough to grow
with your ambitions.

<table>
    <thead>
        <tr>
            <th>Supported Servers</th>
            <th>Supported Integrations</th>
        </tr>
    </thead>
    <tbody>
        <tr>
        <td>
            <a href="https://reactpy-docs.herokuapp.com/docs/guides/getting-started/installing-reactpy.html#officially-supported-servers">
                Flask, FastAPI, Sanic, Tornado
            </a>
        </td>
        <td>
            <a href="https://github.com/reactive-python/reactpy-django">Django</a>,
            <a href="https://github.com/reactive-python/reactpy-jupyter">Jupyter</a>,
            <a href="https://github.com/reactive-python/reactpy-dash">Plotly-Dash</a>
        </td>
        </tr>
    </tbody>
</table>

# At a Glance

To get a rough idea of how to write apps in ReactPy, take a look at this tiny _Hello World_ application.

```python
from reactpy import component, html, run

@component
def HelloWorld():
    return html.h1("Hello, World!")

run(HelloWorld)
```

# Resources

Follow the links below to find out more about this project.

- [Try it Now](https://mybinder.org/v2/gh/reactive-python/reactpy-jupyter/main?urlpath=lab/tree/notebooks/introduction.ipynb) - check out ReactPy in a Jupyter Notebook.
- [Documentation](https://reactpy-docs.herokuapp.com/) - learn how to install, run, and use ReactPy.
- [Community Forum](https://github.com/reactive-python/reactpy/discussions) - ask questions, share ideas, and show off projects.
- [Contributor Guide](https://reactpy-docs.herokuapp.com/docs/developing-reactpy/contributor-guide.html) - see how you can help develop this project.
- [Code of Conduct](https://github.com/reactive-python/reactpy/blob/main/CODE_OF_CONDUCT.md) - standards for interacting with this community.
